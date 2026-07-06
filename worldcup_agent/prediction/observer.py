"""Tournament Observer — The Agent's Sensory System.

This module provides the "Observe" step in the Agent loop:
  1. Fetch real match results from data sources
  2. Detect new information (injuries, news, schedule changes)
  3. Return observations that trigger the reasoning/update cycle
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from worldcup_agent.prediction.world_state import MatchResult, WorldState, load_world_state, save_world_state


# ── Observation Types ───────────────────────────────────────────────────────────

@dataclass
class Observation:
    """One unit of new information for the Agent."""
    obs_type: Literal[
        "match_result",
        "bracket_update",
        "team_news",
        "schedule_change",
        "no_new_data",
    ]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict = field(default_factory=dict)
    priority: Literal["high", "medium", "low"] = "medium"

    def __str__(self) -> str:
        return f"[{self.obs_type}] {self.data.get('summary', '')}"


@dataclass
class ObservationSet:
    """Collection of observations from one observation cycle."""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    observations: list[Observation] = field(default_factory=list)

    @property
    def has_new_data(self) -> bool:
        return any(o.obs_type != "no_new_data" for o in self.observations)

    @property
    def high_priority(self) -> list[Observation]:
        return [o for o in self.observations if o.priority == "high"]

    def summary(self) -> str:
        if not self.observations:
            return "No observations"
        return "; ".join(str(o) for o in self.observations)


# ── Data Sources ────────────────────────────────────────────────────────────────

# Path to the live results file (would come from data scraper in production)
LIVE_RESULTS_FILE = (
    Path(__file__).resolve().parents[2] / "data" / "cache" / "live_results.json"
)


class LiveResultsSource:
    """
    Reads real match results from local file.

    In production, this would query:
    - Official FIFA API
    - Sports data providers (SportRadar, Opta)
    - Web scrapers for match scores
    """

    def __init__(self, data_path: Path | None = None):
        self.data_path = data_path or LIVE_RESULTS_FILE

    def read_results(self) -> list[MatchResult]:
        """Read all match results from the live data file."""
        if not self.data_path.exists():
            return []

        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            results = []

            for item in data.get("matches", []):
                results.append(MatchResult(
                    match_id=item["match_id"],
                    home_team=item["home_team"],
                    away_team=item["away_team"],
                    home_score=item.get("home_score", 0),
                    away_score=item.get("away_score", 0),
                    stage=item.get("stage", "group"),
                    kickoff=item.get("kickoff", ""),
                ))

            return results
        except Exception:
            return []


# ── News Source ────────────────────────────────────────────────────────────────

NEWS_FILE = (
    Path(__file__).resolve().parents[2] / "data" / "cache" / "news_impact.json"
)


@dataclass
class TeamNews:
    """News about a team (injuries, suspensions, etc.)."""
    team: str
    news_type: Literal["injury", "suspension", "form", "other"]
    severity: float  # 0 to 1, higher = more negative impact
    description: str
    source: str
    published_at: str


class NewsSource:
    """
    Reads team news from local file.

    In production, this would call:
    - Sports news APIs
    - Team official announcements
    - Social media monitoring
    """

    def __init__(self, data_path: Path | None = None):
        self.data_path = data_path or NEWS_FILE

    def read_news(self) -> list[TeamNews]:
        """Read team news from file."""
        if not self.data_path.exists():
            return []

        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            news_list = []

            for item in data.get("news", []):
                news_list.append(TeamNews(
                    team=item["team"],
                    news_type=item.get("news_type", "other"),
                    severity=item.get("severity", 0.0),
                    description=item.get("description", ""),
                    source=item.get("source", ""),
                    published_at=item.get("published_at", ""),
                ))

            return news_list
        except Exception:
            return []

    def news_impact_summary(self) -> dict[str, float]:
        """Return team -> impact score mapping."""
        news = self.read_news()
        impacts: dict[str, float] = {}

        for item in news:
            if item.team not in impacts:
                impacts[item.team] = 0.0
            impacts[item.team] += item.severity

        # Normalize: cap at -0.3 (30% max penalty)
        for team in impacts:
            impacts[team] = max(-0.3, min(0.0, impacts[team]))

        return impacts


# ── Tournament Observer ────────────────────────────────────────────────────────

class TournamentObserver:
    """
    The Agent's sensory system.

    Observes the world and returns what changed.
    This is the "Observe" step in: Observe → Reason → Act → Observe...
    """

    def __init__(
        self,
        live_source: LiveResultsSource | None = None,
        news_source: NewsSource | None = None,
    ):
        self.live_source = live_source or LiveResultsSource()
        self.news_source = news_source or NewsSource()

    def observe(self, previous_state: WorldState | None = None) -> ObservationSet:
        """
        Gather all new observations since last check.

        Returns ObservationSet with all new information.
        """
        observations: list[Observation] = []
        prev_state = previous_state or load_world_state()

        # 1. Check for new match results
        new_results = self._observe_results(prev_state)
        observations.extend(new_results)

        # 2. Check for team news
        news_impact = self._observe_news()
        observations.extend(news_impact)

        # 3. Check for schedule changes (placeholder)
        schedule_changes = self._observe_schedule()
        observations.extend(schedule_changes)

        # 4. If no observations, return no-data
        if not observations:
            observations.append(Observation(
                obs_type="no_new_data",
                data={"summary": "No new tournament data available"},
                priority="low",
            ))

        return ObservationSet(observations=observations)

    def _observe_results(self, prev_state: WorldState | None) -> list[Observation]:
        """Check for new match results."""
        observations: list[Observation] = []
        current_results = self.live_source.read_results()

        if not current_results:
            return observations

        # Get IDs of results we already know
        known_ids: set[str] = set()
        if prev_state:
            known_ids = {r.match_id for r in prev_state.results}

        # Find new results
        for result in current_results:
            if result.match_id not in known_ids:
                observations.append(Observation(
                    obs_type="match_result",
                    data={
                        "match_id": result.match_id,
                        "summary": f"{result.home_team} {result.home_score} - {result.away_score} {result.away_team}",
                        "winner": result.winner,
                        "stage": result.stage,
                        **result.to_dict(),
                    },
                    priority="high" if result.stage in ("qf", "sf", "final") else "medium",
                ))

        return observations

    def _observe_news(self) -> list[Observation]:
        """Check for team news (injuries, etc.)."""
        observations: list[Observation] = []
        news_list = self.news_source.read_news()

        for news in news_list:
            observations.append(Observation(
                obs_type="team_news",
                data={
                    "team": news.team,
                    "summary": f"{news.team}: {news.description}",
                    "severity": news.severity,
                    "type": news.news_type,
                    "source": news.source,
                },
                priority="high" if news.severity > 0.5 else "medium" if news.severity > 0.2 else "low",
            ))

        return observations

    def _observe_schedule(self) -> list[Observation]:
        """Check for schedule changes (placeholder)."""
        # In production: query official schedule for changes
        return []


# ── Simulator Observer (for testing) ─────────────────────────────────────────

class SimulatedObserver(TournamentObserver):
    """
    Simulates match results for testing/demonstration.

    When real data isn't available, this generates plausible results
    based on Elo ratings to show the Agent's feedback loop in action.
    """

    def __init__(self, elo_map: dict[str, float] | None = None):
        super().__init__()
        self.elo_map = elo_map or {}

    def simulate_result(
        self,
        home_team: str,
        away_team: str,
        elo_home: float | None = None,
        elo_away: float | None = None,
    ) -> tuple[int, int]:
        """
        Simulate a match result based on Elo ratings.

        Returns (home_score, away_score).
        """
        import random

        h_elo = elo_home or self.elo_map.get(home_team, 1500)
        a_elo = elo_away or self.elo_map.get(away_team, 1500)

        # Probability of home winning
        p_win = 1.0 / (1.0 + 10 ** ((a_elo - h_elo) / 400))
        p_draw = 0.25 * (1.0 - abs(h_elo - a_elo) / 800)
        p_draw = max(0.10, min(0.28, p_draw))

        roll = random.random()

        if roll < p_win:
            # Home wins
            goal_diff = max(1, int(abs(h_elo - a_elo) / 150) + 1)
            return (random.randint(1, 2 + goal_diff), random.randint(0, 1))
        elif roll < p_win + p_draw:
            # Draw
            return (random.randint(0, 2), random.randint(0, 2))
        else:
            # Away wins
            goal_diff = max(1, int(abs(a_elo - h_elo) / 150) + 1)
            return (random.randint(0, 1), random.randint(1, 2 + goal_diff))
