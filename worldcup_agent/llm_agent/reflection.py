"""LLM reflection pass for checking prediction consistency without overwriting outcomes."""

from __future__ import annotations

import json
import time
from typing import Any, Iterable

from worldcup_agent.llm_agent.llm_client import LLMClientError, OpenAICompatibleChatClient, parse_json_object


PROMPT_VERSION = "prediction_reflection_v1"
SYSTEM_PROMPT = """你是世界杯预测反思 Agent。评估输入中每场预测是否自洽，而不是重新预测或输出思维链。重点检查：
1. 胜者、比分与胜平负概率是否一致；
2. 预测原因是否确实引用了球队画像、教练、球员或主客场等证据；
3. LLM 概率是否相对 probability_model_baseline 有无法解释的偏离；
4. 淘汰赛队伍是否来自前一轮胜者。
仅输出 JSON：
{
  "reviews": [
    {
      "match_id": "输入 id",
      "verdict": "pass|caution|inconsistent",
      "logic_score": 0-100,
      "summary": "不超过80字中文结论",
      "checks": [
        {"dimension": "probability|score|evidence|bracket", "verdict": "pass|caution|inconsistent", "note": "不超过50字"}
      ]
    }
  ]
}"""


class LLMPredictionReflector:
    """Reviews compact batches of matches and stores review artifacts on each match."""

    def __init__(self, client: OpenAICompatibleChatClient | None, *, require_llm: bool = False) -> None:
        self.client = client
        self.require_llm = require_llm

    def review_snapshot(
        self,
        snapshot: dict[str, Any],
        *,
        batch_size: int = 6,
        request_delay_seconds: float = 0.0,
    ) -> tuple[int, int]:
        matches = list(_iter_matches(snapshot))
        reviews_written = 0
        requests = 0
        for index in range(0, len(matches), batch_size):
            batch = matches[index : index + batch_size]
            payload = {"matches": [_match_payload(match) for match in batch]}
            if self.client is None:
                if self.require_llm:
                    raise LLMClientError("No LLM client configured for prediction reflection.")
                raw_reviews = [_fallback_review(match) for match in batch]
            else:
                result = self.client.chat(SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, indent=2))
                raw_reviews = parse_json_object(result.content).get("reviews", [])
                requests += 1
            by_id = {
                item.get("match_id"): item
                for item in raw_reviews
                if isinstance(item, dict) and item.get("match_id")
            } if isinstance(raw_reviews, list) else {}
            for match in batch:
                review = _validated_review(by_id.get(match.get("id")), match)
                review.update(
                    {
                        "llm_provider": self.client.provider if self.client else "deterministic_context_fallback",
                        "llm_model": self.client.model if self.client else "deterministic_context_fallback",
                        "llm_prompt_version": PROMPT_VERSION,
                    }
                )
                match["llm_reflection"] = review
                reviews_written += 1
            if request_delay_seconds > 0 and index + batch_size < len(matches):
                time.sleep(request_delay_seconds)
        return reviews_written, requests


def _iter_matches(snapshot: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for group in snapshot.get("group_predictions", {}).values():
        yield from group.get("matches", [])
    rounds = snapshot.get("knockout_predictions", {}).get("rounds", {})
    for key in ("round_of_32", "round_of_16", "quarter_finals", "semi_finals"):
        yield from rounds.get(key, [])
    for key in ("third_place", "final"):
        match = rounds.get(key)
        if isinstance(match, dict):
            yield match


def _match_payload(match: dict[str, Any]) -> dict[str, Any]:
    return {
        "match_id": match.get("id"),
        "stage": match.get("stage"),
        "home_team": match.get("home_team"),
        "away_team": match.get("away_team"),
        "winner": match.get("winner"),
        "predicted_score": match.get("predicted_score"),
        "probabilities": {
            "home": match.get("home_win_prob"),
            "draw": match.get("draw_prob"),
            "away": match.get("away_win_prob"),
        },
        "reasoning": match.get("reasoning"),
        "reasoning_factors": match.get("llm_reasoning_factors", []),
        "probability_model_baseline": match.get("probability_model", {}),
    }


def _fallback_review(match: dict[str, Any]) -> dict[str, Any]:
    home, draw, away = _probabilities(match)
    winner = match.get("winner")
    expected = match.get("home_team") if home >= max(draw, away) else match.get("away_team") if away >= max(home, draw) else "Draw"
    score_consistent = _score_supports_winner(match.get("predicted_score"), winner, match.get("home_team"), match.get("away_team"))
    probability_consistent = winner == expected and abs(home + draw + away - 1) < 0.03
    verdict = "pass" if score_consistent and probability_consistent else "caution"
    return {
        "match_id": match.get("id"),
        "verdict": verdict,
        "logic_score": 86 if verdict == "pass" else 64,
        "summary": "降级反思已校验比分、胜者与概率的一致性；未执行 LLM 证据语义复核。",
        "checks": [
            {"dimension": "probability", "verdict": "pass" if probability_consistent else "caution", "note": "胜者与概率排序已进行规则校验。"},
            {"dimension": "score", "verdict": "pass" if score_consistent else "caution", "note": "比分与胜者已进行规则校验。"},
            {"dimension": "evidence", "verdict": "caution", "note": "需要真实 LLM 才能完成证据语义复核。"},
        ],
    }


def _validated_review(raw: Any, match: dict[str, Any]) -> dict[str, Any]:
    fallback = _fallback_review(match)
    if not isinstance(raw, dict):
        return fallback
    verdict = str(raw.get("verdict") or "").lower()
    if verdict not in {"pass", "caution", "inconsistent"}:
        verdict = fallback["verdict"]
    try:
        logic_score = round(max(0.0, min(100.0, float(raw.get("logic_score")))), 1)
    except (TypeError, ValueError):
        logic_score = fallback["logic_score"]
    checks = []
    for item in raw.get("checks", []) if isinstance(raw.get("checks"), list) else []:
        if not isinstance(item, dict):
            continue
        dimension = str(item.get("dimension") or "").lower()
        item_verdict = str(item.get("verdict") or "").lower()
        if dimension in {"probability", "score", "evidence", "bracket"} and item_verdict in {"pass", "caution", "inconsistent"}:
            checks.append({"dimension": dimension, "verdict": item_verdict, "note": str(item.get("note") or "")[:100]})
    return {
        "verdict": verdict,
        "logic_score": logic_score,
        "summary": str(raw.get("summary") or fallback["summary"])[:240],
        "checks": checks or fallback["checks"],
    }


def _probabilities(match: dict[str, Any]) -> tuple[float, float, float]:
    values = []
    for key in ("home_win_prob", "draw_prob", "away_win_prob"):
        raw = str(match.get(key) or "0").strip().rstrip("%")
        try:
            value = float(raw)
            values.append(value / 100 if value > 1 else value)
        except ValueError:
            values.append(0.0)
    return tuple(values)  # type: ignore[return-value]


def _score_supports_winner(score: Any, winner: Any, home: Any, away: Any) -> bool:
    try:
        home_goals, away_goals = (int(part.strip()) for part in str(score).split("-", 1))
    except (TypeError, ValueError):
        return False
    expected = home if home_goals > away_goals else away if away_goals > home_goals else "Draw"
    return expected == winner
