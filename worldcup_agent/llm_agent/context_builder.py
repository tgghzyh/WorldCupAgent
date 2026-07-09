"""Build compact match contexts from DataForAgent and local knowledge files."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from worldcup_agent.data_layer import load_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "snapshots" / "latest.json"
TEAM_ENRICHED_PATH = PROJECT_ROOT / "worldcup_agent" / "data_layer" / "cleaned" / "teams_2026_enriched.json"
FRONTEND_KNOWLEDGE = PROJECT_ROOT / "frontend" / "src" / "knowledge"

TEAM_ZH_TO_EN = {
    "阿根廷": "Argentina",
    "墨西哥": "Mexico",
    "厄瓜多尔": "Ecuador",
    "牙买加": "Jamaica",
    "西班牙": "Spain",
    "荷兰": "Netherlands",
    "喀麦隆": "Cameroon",
    "卡塔尔": "Qatar",
    "英格兰": "England",
    "美国": "USA",
    "伊朗": "Iran",
    "威尔士": "Wales",
    "巴西": "Brazil",
    "葡萄牙": "Portugal",
    "塞尔维亚": "Serbia",
    "加纳": "Ghana",
    "德国": "Germany",
    "日本": "Japan",
    "澳大利亚": "Australia",
    "加拿大": "Canada",
    "法国": "France",
    "丹麦": "Denmark",
    "突尼斯": "Tunisia",
    "秘鲁": "Peru",
    "比利时": "Belgium",
    "克罗地亚": "Croatia",
    "摩洛哥": "Morocco",
    "新西兰": "New Zealand",
    "乌拉圭": "Uruguay",
    "哥伦比亚": "Colombia",
    "瑞典": "Sweden",
    "玻利维亚": "Bolivia",
    "意大利": "Italy",
    "奥地利": "Austria",
    "尼日利亚": "Nigeria",
    "希腊": "Greece",
    "塞内加尔": "Senegal",
    "埃及": "Egypt",
    "南非": "South Africa",
    "捷克": "Czech Republic",
    "韩国": "South Korea",
}


@dataclass
class MatchContext:
    match_id: str
    stage: str
    home_team: str
    away_team: str
    scheduled_date: str | None
    prior_prediction: dict[str, Any]
    home_profile: dict[str, Any]
    away_profile: dict[str, Any]
    data_sources: list[str]

    def as_prompt_payload(self) -> dict[str, Any]:
        return {
            "match": {
                "id": self.match_id,
                "stage": self.stage,
                "home_team": self.home_team,
                "away_team": self.away_team,
                "scheduled_date": self.scheduled_date,
            },
            "prior_numeric_prediction": self.prior_prediction,
            "home_team_context": self.home_profile,
            "away_team_context": self.away_profile,
            "data_sources": self.data_sources,
        }


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def _team_id(name: str) -> str:
    aliases = {
        "usa": "usa",
        "united states": "usa",
        "new zealand": "new_zealand",
        "south korea": "south_korea",
        "ivory coast": "ivory_coast",
        "burkina faso": "burkina_faso",
        "costa rica": "costa_rica",
        "south africa": "south_africa",
    }
    normalized = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return aliases.get(normalized, normalized.replace(" ", "_"))


def _compact_text(value: str | None, limit: int = 360) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


class DataForAgentContextBuilder:
    """Creates LLM-ready evidence bundles for each snapshot match."""

    def __init__(self, snapshot_path: Path = SNAPSHOT_PATH) -> None:
        self.snapshot_path = snapshot_path
        self.snapshot = _load_json(snapshot_path)
        self.squad = load_dataset("wc2026_squad")
        self.worldcup = load_dataset("worldcup")
        self.enriched = _load_json(TEAM_ENRICHED_PATH)
        self.coaches = _load_json(FRONTEND_KNOWLEDGE / "coaches_knowledge.json").get("coaches", {})
        self.players = _load_json(FRONTEND_KNOWLEDGE / "players_knowledge.json").get("players", {})

        self.enriched_by_name = {
            item.get("team_2026_name"): item
            for item in self.enriched.get("teams", [])
            if item.get("team_2026_name")
        }
        self.squad_by_en_name = self._build_squad_index()

    def _build_squad_index(self) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for group_name, group in self.squad.get("squads", {}).items():
            for raw_name, data in group.items():
                english_name = TEAM_ZH_TO_EN.get(raw_name, raw_name)
                team_data = {
                    "source_group": group_name,
                    "raw_team_name": raw_name,
                    "coach": data.get("coach"),
                    "players": data.get("players", [])[:12],
                }
                indexed[raw_name] = team_data
                indexed[english_name] = team_data
        return indexed

    def _knowledge_coach(self, team_name: str) -> dict[str, Any] | None:
        target = _team_id(team_name)
        for coach in self.coaches.values():
            if coach.get("team_id") == target:
                tactical = coach.get("coaching_tactical", {})
                return {
                    "name": coach.get("names", {}).get("zh") or coach.get("names", {}).get("en"),
                    "tactical_style": tactical.get("style_zh") or tactical.get("style_en"),
                    "tactical_score": coach.get("ai_tactical_score"),
                    "achievements": coach.get("achievements_zh", [])[:2],
                }
        return None

    def _knowledge_players(self, team_name: str) -> list[dict[str, Any]]:
        target = _team_id(team_name)
        players = [
            player
            for player in self.players.values()
            if isinstance(player, dict) and player.get("team_id") == target
        ]
        players.sort(
            key=lambda p: (
                p.get("ai_impact", {}).get("overall", 0)
                or p.get("ai_impact", {}).get("score", 0)
                or 0
            ),
            reverse=True,
        )
        return [
            {
                "name": p.get("names", {}).get("zh") or p.get("names", {}).get("en"),
                "position": p.get("position_zh") or p.get("position"),
                "club": p.get("club"),
                "highlights": p.get("highlights_zh", [])[:2],
            }
            for p in players[:5]
        ]

    def team_profile(self, team_name: str) -> dict[str, Any]:
        enriched = self.enriched_by_name.get(team_name, {})
        squad = self.squad_by_en_name.get(team_name, {})
        knowledge_coach = self._knowledge_coach(team_name)
        raw_players = squad.get("players", [])
        squad_players = [
            {
                "name": p.get("name") or p.get("player"),
                "position": p.get("position"),
                "club": p.get("club"),
                "caps": p.get("caps"),
                "goals": p.get("goals"),
                "age": p.get("age"),
                "is_captain": p.get("is_captain"),
            }
            for p in raw_players[:5]
            if isinstance(p, dict)
        ]

        return {
            "team": team_name,
            "group": enriched.get("group") or squad.get("source_group"),
            "fifa_rank": enriched.get("world_rank_live") or enriched.get("fifa_ranking_final"),
            "elo": enriched.get("elo_rating_live") or enriched.get("elo_rating"),
            "ranking_source": enriched.get("ranking_source"),
            "coach": squad.get("coach") or (knowledge_coach or {}).get("name"),
            "coach_profile": knowledge_coach,
            "key_players": squad_players or self._knowledge_players(team_name),
            "team_summary": _compact_text(enriched.get("wiki_extract")),
            "data_coverage": {
                "has_dataforagent_squad": bool(squad),
                "has_enriched_profile": bool(enriched),
                "historical_worldcup_matches": self.worldcup.get("metadata", {}).get("totals", {}).get("matches"),
            },
        }

    def iter_snapshot_matches(self) -> list[tuple[str, str, dict[str, Any], MatchContext]]:
        contexts: list[tuple[str, str, dict[str, Any], MatchContext]] = []

        for group_key, group in self.snapshot.get("group_predictions", {}).items():
            for match in group.get("matches", []):
                contexts.append((group_key, "group", match, self._context_for(match)))

        rounds = self.snapshot.get("knockout_predictions", {}).get("rounds", {})
        for round_key in ("round_of_32", "round_of_16", "quarter_finals", "semi_finals"):
            for match in rounds.get(round_key, []):
                contexts.append((round_key, "knockout", match, self._context_for(match)))
        for round_key in ("third_place", "final"):
            match = rounds.get(round_key)
            if isinstance(match, dict):
                contexts.append((round_key, "knockout", match, self._context_for(match)))

        return contexts

    def _context_for(self, match: dict[str, Any]) -> MatchContext:
        home = match.get("home_team", "")
        away = match.get("away_team", "")
        return MatchContext(
            match_id=match.get("id", ""),
            stage=match.get("stage") or match.get("match_type", ""),
            home_team=home,
            away_team=away,
            scheduled_date=match.get("scheduled_date"),
            prior_prediction={
                "predicted_score": match.get("predicted_score"),
                "home_win_prob": match.get("home_win_prob"),
                "draw_prob": match.get("draw_prob"),
                "away_win_prob": match.get("away_win_prob"),
                "reasoning": match.get("reasoning"),
            },
            home_profile=self.team_profile(home),
            away_profile=self.team_profile(away),
            data_sources=[
                "DataForAgent/wc2026_squad",
                "DataForAgent/worldcup",
                "worldcup_agent/data_layer/teams_2026_enriched",
                "frontend/src/knowledge",
            ],
        )
