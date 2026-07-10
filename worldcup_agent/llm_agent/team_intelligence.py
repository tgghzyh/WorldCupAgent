"""Extract structured 2026 team intelligence from DataForAgent evidence."""

from __future__ import annotations

import json
import time
from collections import Counter
from typing import Any

from worldcup_agent.llm_agent.context_builder import DataForAgentContextBuilder
from worldcup_agent.llm_agent.llm_client import LLMClientError, OpenAICompatibleChatClient, parse_json_object


PROMPT_VERSION = "team_intelligence_extraction_v1"
COMPONENTS = (
    "attack",
    "defense",
    "midfield",
    "squad_depth",
    "coach_tactics",
    "tournament_experience",
    "form",
)

SYSTEM_PROMPT = """你是世界杯赛前数据特征提炼 Agent。请仅根据输入的 DataForAgent 名单、教练、球员履历、排名/Elo 和本地球队资料，构建球队在 2026 世界杯的可解释实力画像。不要编造伤病、近期赛果或未提供的事实；数据不足时在 risks/evidence 中明确说明。仅输出 JSON：
{
  "teams": [
    {
      "team": "原样保留输入队名",
      "overall_strength": 0-100,
      "components": {"attack": 0-100, "defense": 0-100, "midfield": 0-100, "squad_depth": 0-100, "coach_tactics": 0-100, "tournament_experience": 0-100, "form": 0-100},
      "tactical_profile": "不超过60字中文",
      "strengths": ["不超过3项"],
      "risks": ["不超过3项"],
      "key_players": ["不超过5名，优先输入名单中球员"],
      "summary": "80-140字中文摘要",
      "evidence": ["不超过3条，说明使用了哪些输入信号"],
      "data_confidence": "High|Medium|Low"
    }
  ]
}"""


class TeamIntelligenceExtractor:
    """Uses one LLM request per group so the full input remains compact and auditable."""

    def __init__(self, client: OpenAICompatibleChatClient | None, *, require_llm: bool = False) -> None:
        self.client = client
        self.require_llm = require_llm

    def extract_all(
        self,
        builder: DataForAgentContextBuilder,
        *,
        request_delay_seconds: float = 0.0,
    ) -> tuple[dict[str, dict[str, Any]], int]:
        grouped = self._teams_by_group(builder)
        output: dict[str, dict[str, Any]] = {}
        requests = 0
        for index, teams in enumerate(grouped.values()):
            payload = {"teams": [self._source_payload(builder, name) for name in teams]}
            if self.client is None:
                if self.require_llm:
                    raise LLMClientError("No LLM client configured for team intelligence extraction.")
                extracted = [self._fallback_profile(team) for team in payload["teams"]]
            else:
                result = self.client.chat(SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, indent=2))
                extracted = parse_json_object(result.content).get("teams", [])
                requests += 1
            for source in payload["teams"]:
                profile = self._validated_profile(
                    self._find_team_profile(extracted, source["team"]),
                    source,
                    provider=self.client.provider if self.client else "deterministic_context_fallback",
                    model=self.client.model if self.client else "deterministic_context_fallback",
                )
                output[source["team"]] = profile
            if request_delay_seconds > 0 and index < len(grouped) - 1:
                time.sleep(request_delay_seconds)
        return output, requests

    @staticmethod
    def _teams_by_group(builder: DataForAgentContextBuilder) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for group_name, group in builder.snapshot.get("group_predictions", {}).items():
            result[group_name] = [row.get("team") for row in group.get("standings", []) if row.get("team")]
        return result

    def _source_payload(self, builder: DataForAgentContextBuilder, team: str) -> dict[str, Any]:
        profile = builder.team_profile(team)
        squad = builder.squad_by_en_name.get(team, {})
        players = [player for player in squad.get("players", []) if isinstance(player, dict)]
        positions = Counter(str(player.get("position") or "Unknown") for player in players)
        experienced = sorted(players, key=lambda player: _number(player.get("caps")), reverse=True)[:8]
        return {
            "team": team,
            "group": profile.get("group"),
            "ranking": {"fifa_rank": profile.get("fifa_rank"), "elo": profile.get("elo")},
            "coach": profile.get("coach"),
            "coach_profile": profile.get("coach_profile"),
            "squad_metrics": {
                "player_count": len(players),
                "position_counts": dict(positions),
                "average_caps": round(_mean([_number(player.get("caps")) for player in players]), 1),
                "average_age": round(_mean([_number(player.get("age")) for player in players]), 1),
                "total_international_goals": round(sum(_number(player.get("goals")) for player in players), 1),
            },
            "experienced_players": [
                {
                    "name": player.get("name") or player.get("player"),
                    "position": player.get("position"),
                    "caps": player.get("caps"),
                    "goals": player.get("goals"),
                    "club": player.get("club"),
                    "captain": bool(player.get("is_captain")),
                }
                for player in experienced
            ],
            "team_summary": profile.get("team_summary"),
            "data_coverage": profile.get("data_coverage"),
        }

    @staticmethod
    def _find_team_profile(items: Any, team: str) -> dict[str, Any]:
        if not isinstance(items, list):
            return {}
        for item in items:
            if isinstance(item, dict) and item.get("team") == team:
                return item
        return {}

    def _validated_profile(
        self,
        raw: dict[str, Any],
        source: dict[str, Any],
        *,
        provider: str,
        model: str,
    ) -> dict[str, Any]:
        fallback = self._fallback_profile(source)
        if not isinstance(raw, dict):
            raw = {}
        components = raw.get("components") if isinstance(raw.get("components"), dict) else {}
        cleaned_components = {
            name: _score(components.get(name), fallback["components"][name])
            for name in COMPONENTS
        }
        return {
            "team": source["team"],
            "group": source.get("group"),
            "ranking": source.get("ranking", {}),
            "overall_strength": _score(raw.get("overall_strength"), fallback["overall_strength"]),
            "components": cleaned_components,
            "tactical_profile": _text(raw.get("tactical_profile"), fallback["tactical_profile"], 120),
            "strengths": _string_list(raw.get("strengths"), fallback["strengths"], 3),
            "risks": _string_list(raw.get("risks"), fallback["risks"], 3),
            "key_players": _string_list(raw.get("key_players"), fallback["key_players"], 5),
            "summary": _text(raw.get("summary"), fallback["summary"], 280),
            "evidence": _string_list(raw.get("evidence"), fallback["evidence"], 3),
            "data_confidence": _confidence(raw.get("data_confidence")),
            "source": "DataForAgent + local enriched team evidence",
            "llm_provider": provider,
            "llm_model": model,
            "llm_prompt_version": PROMPT_VERSION,
        }

    def _fallback_profile(self, source: dict[str, Any]) -> dict[str, Any]:
        rank = _number(source.get("ranking", {}).get("fifa_rank"), 80)
        elo = _number(source.get("ranking", {}).get("elo"), 1500)
        metrics = source.get("squad_metrics", {})
        average_caps = _number(metrics.get("average_caps"), 12)
        player_count = _number(metrics.get("player_count"), 23)
        rank_score = max(25.0, min(95.0, 96 - (rank - 1) * 0.9))
        elo_score = max(25.0, min(95.0, 50 + (elo - 1500) / 8))
        experience = max(30.0, min(92.0, 38 + average_caps * 1.35))
        depth = max(35.0, min(88.0, 42 + player_count * 1.4))
        overall = round(rank_score * 0.28 + elo_score * 0.42 + experience * 0.20 + depth * 0.10, 1)
        key_players = [str(player.get("name")) for player in source.get("experienced_players", []) if player.get("name")][:5]
        return {
            "overall_strength": overall,
            "components": {
                "attack": round((overall + experience) / 2, 1),
                "defense": round(overall * 0.97, 1),
                "midfield": round(overall, 1),
                "squad_depth": round(depth, 1),
                "coach_tactics": 55.0,
                "tournament_experience": round(experience, 1),
                "form": round((overall + elo_score) / 2, 1),
            },
            "tactical_profile": "基于名单经验、排名和 Elo 的保守赛前画像。",
            "strengths": ["排名/Elo 基线", "国际比赛经验", "名单完整度"],
            "risks": ["未接入实时伤病与近期赛果"],
            "key_players": key_players,
            "summary": f"{source['team']} 的降级画像由赛前排名、Elo、名单人数与国家队经验构成，需由 LLM 进一步补充战术语境。",
            "evidence": ["DataForAgent 名单", "FIFA 排名/Elo", "球员出场与进球统计"],
            "data_confidence": "Medium",
        }


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _score(value: Any, default: float) -> float:
    return round(max(0.0, min(100.0, _number(value, default))), 1)


def _text(value: Any, default: str, limit: int) -> str:
    text = str(value or "").strip()
    return text[:limit] if text else default


def _string_list(value: Any, default: list[str], limit: int) -> list[str]:
    if not isinstance(value, list):
        return default[:limit]
    result = [str(item).strip() for item in value if str(item).strip()]
    return result[:limit] or default[:limit]


def _confidence(value: Any) -> str:
    normalized = str(value or "").title()
    return normalized if normalized in {"High", "Medium", "Low"} else "Medium"
