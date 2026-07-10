"""LLM-first match predictor with strict JSON output validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from worldcup_agent.llm_agent.context_builder import MatchContext
from worldcup_agent.llm_agent.llm_client import (
    LLMClientError,
    OpenAICompatibleChatClient,
    parse_json_object,
)


PROMPT_VERSION = "llm_match_prediction_v3_monte_carlo_weighted"
ALLOWED_FACTOR_TYPES = {"fitness", "tactical", "injury", "home", "form", "transition"}

SYSTEM_PROMPT = """你是世界杯冠军预测 Agent 中的比赛分析专家。
你必须根据输入的 DataForAgent 赛前数据、球队资料、教练资料、关键球员和主客场/赛程因素，预测单场比赛。
输入中的 probability_model_baseline 由球队画像分项、Elo、排名和主队调整构成，必须作为概率起点；如需明显偏离，必须在 reasoning 中说明数据依据。
不要输出思维链，只输出可解析 JSON。
原因必须覆盖这些因素中的至少三类：执教教练/战术、关键球员、主客场或旅行、近期/历史状态、伤病或阵容不确定性。
JSON schema:
{
  "winner": "home|away|draw",
  "predicted_score": "2-1",
  "home_win_prob": 0.58,
  "draw_prob": 0.22,
  "away_win_prob": 0.20,
  "confidence": "High|Medium|Low",
  "reasoning": "80-160字中文摘要",
  "reasoning_factors": [
    {"type": "tactical|form|home|fitness|injury|transition", "label": "中文短标题", "description": "中文原因", "weight": 0.25}
  ]
}
概率必须是 0-1 小数，三项合计约等于 1。
若 match.match_type 为 knockout，winner 只能是 home 或 away，且 predicted_score 必须体现同一支胜队；不要输出平局或未说明的点球结果。"""


@dataclass
class MatchPrediction:
    winner: str
    predicted_score: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    confidence: str
    reasoning: str
    reasoning_factors: list[dict[str, Any]]
    probability_model: dict[str, Any]
    monte_carlo_prior: dict[str, Any]
    model: str
    provider: str
    prompt_version: str = PROMPT_VERSION

    def as_snapshot_update(self) -> dict[str, Any]:
        return {
            "predicted_score": self.predicted_score,
            "home_win_prob": _format_prob(self.home_win_prob),
            "draw_prob": _format_prob(self.draw_prob),
            "away_win_prob": _format_prob(self.away_win_prob),
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "llm_reasoning_factors": self.reasoning_factors,
            "probability_model": self.probability_model,
            "monte_carlo_prior": self.monte_carlo_prior,
            "llm_model": self.model,
            "llm_provider": self.provider,
            "llm_prompt_version": self.prompt_version,
        }


class LLMMatchPredictor:
    """Predicts matches with a real LLM when configured, fallback otherwise."""

    def __init__(
        self,
        client: OpenAICompatibleChatClient | None,
        *,
        require_llm: bool = False,
    ) -> None:
        self.client = client
        self.require_llm = require_llm

    def predict(self, context: MatchContext) -> MatchPrediction:
        if self.client is None:
            if self.require_llm:
                raise LLMClientError(
                    "No LLM client configured. Set LLM_API_KEY, OPENAI_API_KEY, or DASHSCOPE_API_KEY."
                )
            return self._fallback_prediction(context, "no_api_key_fallback")

        user_prompt = json.dumps(context.as_prompt_payload(), ensure_ascii=False, indent=2)
        result = self.client.chat(SYSTEM_PROMPT, user_prompt)
        parsed = parse_json_object(result.content)
        return self._prediction_from_dict(parsed, context, result.model, result.provider)

    def _prediction_from_dict(
        self,
        raw: dict[str, Any],
        context: MatchContext,
        model: str,
        provider: str,
    ) -> MatchPrediction:
        raw_home, raw_draw, raw_away = _normalize_probs(
            _to_probability(raw.get("home_win_prob")),
            _to_probability(raw.get("draw_prob")),
            _to_probability(raw.get("away_win_prob")),
        )
        home, draw, away = _blend_with_monte_carlo(
            raw_home,
            raw_draw,
            raw_away,
            context.monte_carlo_prior,
        )
        winner = _winner_from_probabilities(
            home,
            draw,
            away,
            is_knockout=context.match_type == "knockout",
        )

        confidence = str(raw.get("confidence") or _confidence_from_probs(home, draw, away)).title()
        if confidence not in {"High", "Medium", "Low"}:
            confidence = _confidence_from_probs(home, draw, away)

        factors = _clean_factors(raw.get("reasoning_factors"), context)
        score, winner = _normalize_result(
            str(raw.get("predicted_score") or _score_from_winner(winner)),
            winner,
            home,
            draw,
            away,
            is_knockout=context.match_type == "knockout",
        )
        reasoning = str(raw.get("reasoning") or "").strip()
        if len(reasoning) < 20:
            reasoning = _fallback_reasoning(context, winner)
        elif (raw_home, raw_draw, raw_away) != (home, draw, away):
            reasoning = (
                f"{reasoning} 蒙特卡洛赛程先验按 "
                f"{context.monte_carlo_prior.get('llm_prediction_weight', 0) * 100:.0f}% 权重校准最终概率。"
            )

        return MatchPrediction(
            winner=winner,
            predicted_score=score,
            home_win_prob=home,
            draw_prob=draw,
            away_win_prob=away,
            confidence=confidence,
            reasoning=reasoning,
            reasoning_factors=factors,
            probability_model=context.probability_baseline,
            monte_carlo_prior=context.monte_carlo_prior,
            model=model,
            provider=provider,
        )

    def _fallback_prediction(self, context: MatchContext, provider: str) -> MatchPrediction:
        baseline = context.probability_baseline
        home = _to_probability(baseline.get("home_win_prob"))
        draw = _to_probability(baseline.get("draw_prob"))
        away = _to_probability(baseline.get("away_win_prob"))
        home, draw, away = _normalize_probs(home, draw, away)
        home, draw, away = _blend_with_monte_carlo(
            home,
            draw,
            away,
            context.monte_carlo_prior,
        )
        winner = _winner_from_probabilities(
            home,
            draw,
            away,
            is_knockout=context.match_type == "knockout",
        )

        factors = _clean_factors(
            [
                {
                    "type": "tactical",
                    "label": "教练与战术",
                    "description": _coach_factor(context),
                    "weight": 0.28,
                },
                {
                    "type": "form",
                    "label": "球员与实力",
                    "description": _player_factor(context),
                    "weight": 0.30,
                },
                {
                    "type": "home",
                    "label": "主客场与旅途",
                    "description": f"{context.home_team}按赛程列为主队，获得轻微场地与备战便利；{context.away_team}需要适应客队节奏。",
                    "weight": 0.18,
                },
                {
                    "type": "transition",
                    "label": "排名与历史样本",
                    "description": f"ELO/排名差异用于约束概率，历史世界杯样本用于校准不确定性。",
                    "weight": 0.24,
                },
            ],
            context,
        )

        return MatchPrediction(
            winner=winner,
            predicted_score=_score_from_winner(winner),
            home_win_prob=home,
            draw_prob=draw,
            away_win_prob=away,
            confidence=_confidence_from_probs(home, draw, away),
            reasoning=_fallback_reasoning(context, winner),
            reasoning_factors=factors,
            probability_model=baseline,
            monte_carlo_prior=context.monte_carlo_prior,
            model="deterministic_context_fallback",
            provider=provider,
        )


def _to_probability(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value) / 100 if value > 1 else float(value)
    if isinstance(value, str):
        value = value.strip()
        if value.endswith("%"):
            return float(value[:-1]) / 100
        return float(value)
    return 0.0


def _normalize_probs(home: float, draw: float, away: float) -> tuple[float, float, float]:
    values = [max(0.03, min(0.94, v)) for v in (home, draw, away)]
    total = sum(values) or 1.0
    return tuple(round(v / total, 4) for v in values)  # type: ignore[return-value]


def _blend_with_monte_carlo(
    home: float,
    draw: float,
    away: float,
    prior: dict[str, Any],
) -> tuple[float, float, float]:
    if not isinstance(prior, dict) or not prior.get("available"):
        return _normalize_probs(home, draw, away)
    weight = max(0.0, min(1.0, _to_probability(prior.get("llm_prediction_weight"))))
    prior_home = _to_probability(prior.get("home_win_prob"))
    prior_draw = _to_probability(prior.get("draw_prob"))
    prior_away = _to_probability(prior.get("away_win_prob"))
    if weight <= 0 or prior_home + prior_draw + prior_away <= 0:
        return _normalize_probs(home, draw, away)
    return _normalize_probs(
        home * (1 - weight) + prior_home * weight,
        draw * (1 - weight) + prior_draw * weight,
        away * (1 - weight) + prior_away * weight,
    )


def _winner_from_probabilities(
    home: float,
    draw: float,
    away: float,
    *,
    is_knockout: bool,
) -> str:
    if is_knockout:
        return "home" if home >= away else "away"
    return "home" if home >= max(draw, away) else "away" if away >= max(home, draw) else "draw"


def _format_prob(value: float) -> str:
    return f"{value * 100:.1f}%"


def _confidence_from_probs(home: float, draw: float, away: float) -> str:
    spread = max(home, draw, away) - sorted([home, draw, away])[-2]
    if spread >= 0.22:
        return "High"
    if spread >= 0.10:
        return "Medium"
    return "Low"


def _score_from_winner(winner: str) -> str:
    if winner == "home":
        return "2-1"
    if winner == "away":
        return "1-2"
    return "1-1"


def _normalize_result(
    score: str,
    winner: str,
    home_probability: float,
    draw_probability: float,
    away_probability: float,
    *,
    is_knockout: bool,
) -> tuple[str, str]:
    """Make the displayed score and the advancement winner a single coherent result."""

    try:
        home_goals, away_goals = (int(part.strip()) for part in score.split("-", 1))
        if home_goals < 0 or away_goals < 0:
            raise ValueError
    except (TypeError, ValueError):
        home_goals, away_goals = (2, 1) if winner == "home" else (1, 2) if winner == "away" else (1, 1)

    if is_knockout and winner == "draw":
        winner = "home" if home_probability >= away_probability else "away"

    if winner == "home" and home_goals <= away_goals:
        home_goals = away_goals + 1
    elif winner == "away" and away_goals <= home_goals:
        away_goals = home_goals + 1
    elif winner == "draw" and home_goals != away_goals:
        goals = min(home_goals, away_goals)
        home_goals = goals
        away_goals = goals

    score_winner = "home" if home_goals > away_goals else "away" if away_goals > home_goals else "draw"
    if is_knockout and score_winner == "draw":
        winner = "home" if home_probability >= away_probability else "away"
        if winner == "home":
            home_goals += 1
        else:
            away_goals += 1
        score_winner = winner

    return f"{home_goals}-{away_goals}", score_winner


def _num(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_factors(raw: Any, context: MatchContext) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raw = []
    factors: list[dict[str, Any]] = []
    for index, item in enumerate(raw[:5]):
        if not isinstance(item, dict):
            continue
        factor_type = str(item.get("type") or "form").lower()
        if factor_type not in ALLOWED_FACTOR_TYPES:
            factor_type = "form"
        weight = _num(item.get("weight"), 0.2)
        factors.append(
            {
                "id": f"{context.match_id}-llm-{index}",
                "type": factor_type,
                "label": str(item.get("label") or "LLM factor")[:40],
                "description": str(item.get("description") or "")[:280],
                "weight": round(max(0.05, min(0.95, weight)), 3),
            }
        )
    if len(factors) >= 3:
        return factors
    return [
        {
            "id": f"{context.match_id}-coach",
            "type": "tactical",
            "label": "教练与战术",
            "description": _coach_factor(context),
            "weight": 0.30,
        },
        {
            "id": f"{context.match_id}-players",
            "type": "form",
            "label": "关键球员",
            "description": _player_factor(context),
            "weight": 0.32,
        },
        {
            "id": f"{context.match_id}-venue",
            "type": "home",
            "label": "主客场因素",
            "description": f"{context.home_team}为赛程主队，享有轻微备战便利；{context.away_team}的客场适应性会影响节奏。",
            "weight": 0.18,
        },
    ]


def _coach_factor(context: MatchContext) -> str:
    home_coach = context.home_profile.get("coach") or "未知教练"
    away_coach = context.away_profile.get("coach") or "未知教练"
    return f"{context.home_team}由{home_coach}带队，{context.away_team}由{away_coach}带队；战术稳定性和临场调整是主要判断依据。"


def _player_factor(context: MatchContext) -> str:
    def names(profile: dict[str, Any]) -> str:
        players = profile.get("key_players") or []
        selected = [p.get("name") for p in players if isinstance(p, dict) and p.get("name")]
        return "、".join(selected[:3]) or "核心球员数据不足"

    return f"{context.home_team}关键球员：{names(context.home_profile)}；{context.away_team}关键球员：{names(context.away_profile)}。"


def _fallback_reasoning(context: MatchContext, winner: str) -> str:
    outcome = (
        f"看好{context.home_team}小胜"
        if winner == "home"
        else f"看好{context.away_team}客场取胜"
        if winner == "away"
        else "预计双方战平"
    )
    return (
        f"{outcome}。判断综合了DataForAgent赛前资料、教练战术、关键球员、ELO/排名差异和主客场适应因素；"
        "由于伤病与最终名单仍有不确定性，保留概率区间而非绝对结论。"
    )
