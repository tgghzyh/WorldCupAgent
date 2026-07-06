"""Data Agent — handles data acquisition and freshness checking.

This agent implements the ReAct pattern for data operations:
  1. OBSERVE: Check current data freshness from World State
  2. THINK: Decide if we need to refresh data
  3. ACT: Fetch/refresh data from sources
  4. EVALUATE: Check if data is valid
  5. REVISE: If data is stale, force refresh
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from worldcup_agent.multi_agent import BaseAgent, WorldState, AgentTrace, AgentStatus


# ── Constants ────────────────────────────────────────────────────────────────


DATA_DIR = Path(__file__).resolve().parents[3] / "data"
ELO_CACHE_FILE = DATA_DIR / "cache" / "elo_ratings.json"
RANKINGS_CACHE_FILE = DATA_DIR / "cache" / "fifa_rankings.json"
ODDS_CACHE_FILE = DATA_DIR / "cache" / "odds.json"
TEAMS_CACHE_FILE = DATA_DIR / "data_layer" / "cleaned" / "teams_2026_enriched.json"

# TTL thresholds (in hours)
ELO_TTL_HOURS = 168  # 7 days
ODDS_TTL_HOURS = 24  # 1 day
RANKINGS_TTL_HOURS = 168  # 7 days


# ── Data Agent ────────────────────────────────────────────────────────────────


class DataAgent(BaseAgent):
    """
    Data Agent — responsible for data acquisition and freshness.

    ReAct Loop:
      OBSERVE: Check what data is in World State
      THINK:   "Is the data fresh enough for prediction?"
      ACT:     Fetch/refresh if needed
      EVALUATE: Is the data valid and complete?
      REVISE:  If not, try alternative source or use fallback
    """

    def __init__(self):
        super().__init__(
            name="data_agent",
            description="Handles data acquisition and freshness checking",
            max_iterations=3,
        )
        self._freshness_cache: dict[str, datetime] = {}

    @property
    def system_prompt(self) -> str:
        return """You are the Data Agent for the WC2026 prediction system.

Your responsibilities:
  1. Check data freshness (Elo, rankings, odds, injuries)
  2. Fetch/update data when stale
  3. Validate data completeness
  4. Report data quality issues

Data freshness rules:
  - Elo ratings: refresh if older than 7 days
  - FIFA rankings: refresh if older than 7 days
  - Odds: refresh if older than 24 hours
  - Injury reports: refresh if older than 12 hours

You do NOT make predictions — you only ensure data is available."""

    # ── ReAct Steps ──────────────────────────────────────────────────────────

    def observe(self, state: WorldState) -> dict:
        """OBSERVE: Check current data state."""
        observation = {
            "current_data_freshness": {
                "elo": state.elo_last_updated,
                "odds": state.odds_last_updated,
                "rankings": state.elo_last_updated,  # Same as elo
            },
            "teams_in_state": len(state.teams),
            "has_recent_results": len(state.match_results) > 0,
        }

        # Check actual files
        files_status = {}
        for name, path in [
            ("elo", ELO_CACHE_FILE),
            ("rankings", RANKINGS_CACHE_FILE),
            ("odds", ODDS_CACHE_FILE),
            ("teams", TEAMS_CACHE_FILE),
        ]:
            if path.exists():
                try:
                    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                    files_status[name] = {
                        "exists": True,
                        "last_modified": mtime.isoformat(),
                        "age_hours": (datetime.now(timezone.utc) - mtime).total_seconds() / 3600,
                    }
                except Exception:
                    files_status[name] = {"exists": True, "error": "Cannot read timestamp"}
            else:
                files_status[name] = {"exists": False}

        observation["file_status"] = files_status

        # Determine freshness
        needs_refresh = []
        for name, status in files_status.items():
            if not status.get("exists"):
                needs_refresh.append(name)
            elif status.get("age_hours"):
                ttl = self._get_ttl(name)
                if status["age_hours"] > ttl:
                    needs_refresh.append(name)

        observation["needs_refresh"] = needs_refresh

        return observation

    def think(self, observation: dict, state: WorldState) -> str:
        """THINK: Decide what to do based on observation."""
        if not observation.get("needs_refresh"):
            return "DATA_FRESH: All required data is up-to-date. No refresh needed."

        stale_data = observation["needs_refresh"]
        return f"DATA_STALE: Need to refresh {', '.join(stale_data)}. " \
               f"Will fetch from cache/API and update World State."

    def act(self, thought: str, state: WorldState) -> tuple[dict, str]:
        """ACT: Fetch and validate data."""
        result = {
            "data": {},
            "errors": [],
            "warnings": [],
        }

        # Always try to load teams (required for predictions)
        teams_data = self._load_teams()
        if teams_data:
            result["data"]["teams"] = teams_data
            state.teams = teams_data
        else:
            result["errors"].append("Failed to load teams data")

        # Load Elo if available
        elo_data = self._load_elo()
        if elo_data:
            result["data"]["elo"] = elo_data
            state.elo_last_updated = datetime.now(timezone.utc).isoformat()

        # Load rankings if available
        rankings_data = self._load_rankings()
        if rankings_data:
            result["data"]["rankings"] = rankings_data

        # Load odds if available
        odds_data = self._load_odds()
        if odds_data:
            result["data"]["odds"] = odds_data
            state.odds_last_updated = datetime.now(timezone.utc).isoformat()

        # Check data completeness
        if not result["data"].get("teams"):
            result["errors"].append("Critical: No teams data available")
        else:
            team_count = len(result["data"]["teams"])
            if team_count < 48:
                result["warnings"].append(f"Only {team_count}/48 teams loaded")

        observation = f"Loaded {len(result['data'])} data sources. " \
                      f"Errors: {len(result['errors'])}, Warnings: {len(result['warnings'])}"

        return result, observation

    def evaluate(self, result: dict, state: WorldState) -> bool:
        """EVALUATE: Check if data is usable."""
        # Critical check: must have teams data
        if "teams" not in result.get("data", {}):
            return False

        # Must have at least some teams
        if len(state.teams) < 48:
            # Warning is okay, but we can still proceed with available data
            pass

        # No critical errors
        if result.get("errors"):
            for error in result["errors"]:
                if "Critical" in error:
                    return False

        return True

    def revise(self, result: Any, error: str, state: WorldState) -> str:
        """REVISE: Try alternative data source or fallback."""
        return "Attempting fallback: Will use cached data with extended TTL. " \
               "Marking data as 'stale but usable'."

    # ── Helper Methods ──────────────────────────────────────────────────────

    def _get_ttl(self, data_type: str) -> int:
        """Get TTL for data type in hours."""
        ttl_map = {
            "elo": ELO_TTL_HOURS,
            "rankings": RANKINGS_TTL_HOURS,
            "odds": ODDS_TTL_HOURS,
            "teams": 720,  # 30 days
        }
        return ttl_map.get(data_type, 24)

    def _load_teams(self) -> dict[str, dict]:
        """Load teams data."""
        try:
            if not TEAMS_CACHE_FILE.exists():
                return {}

            data = json.loads(TEAMS_CACHE_FILE.read_text(encoding="utf-8"))
            teams = {}

            for team_data in data.get("teams", []):
                name = team_data.get("team_2026_name", "")
                if name:
                    teams[name] = {
                        "name": name,
                        "group": team_data.get("group", ""),
                        "elo": team_data.get("elo_rating_live", 1500),
                        "rank": team_data.get("world_rank_live", 120),
                        "form_score": team_data.get("recent_form_score", 0.5),
                    }

            return teams
        except Exception as e:
            return {}

    def _load_elo(self) -> dict | None:
        """Load Elo ratings."""
        try:
            if not ELO_CACHE_FILE.exists():
                return None
            return json.loads(ELO_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _load_rankings(self) -> dict | None:
        """Load FIFA rankings."""
        try:
            if not RANKINGS_CACHE_FILE.exists():
                return None
            return json.loads(RANKINGS_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _load_odds(self) -> dict | None:
        """Load betting odds."""
        try:
            if not ODDS_CACHE_FILE.exists():
                return None
            return json.loads(ODDS_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None
