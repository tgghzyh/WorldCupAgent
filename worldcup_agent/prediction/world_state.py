"""World State — The Agent's Memory of the Tournament.

This is the CORE of the closed-loop agent. It maintains:
  1. Current bracket state (who qualified, who's left)
  2. Real match results (what actually happened)
  3. Team strength estimates (dynamically updated)
  4. Pending predictions (what we predicted vs reality)

The Agent updates this after each match, then re-predicts remaining games.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from worldcup_agent.tournament.rule import GroupStanding


# ── Match Result ─────────────────────────────────────────────────────────────

@dataclass
class MatchResult:
    """A real match result (home_score, away_score, winner)."""
    match_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    stage: Literal["group", "r32", "r16", "qf", "sf", "third_place", "final"]
    kickoff: str  # ISO datetime

    @property
    def winner(self) -> str | None:
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return None  # draw

    @property
    def loser(self) -> str | None:
        if self.home_score < self.away_score:
            return self.home_team
        elif self.away_score < self.home_score:
            return self.away_team
        return None

    @property
    def is_draw(self) -> bool:
        return self.home_score == self.away_score

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "stage": self.stage,
            "kickoff": self.kickoff,
            "winner": self.winner,
            "is_draw": self.is_draw,
        }


# ── Team State ────────────────────────────────────────────────────────────────

@dataclass
class TeamState:
    """Current state of one team in the tournament."""
    name: str
    elo_rating: float = 1500.0
    group: str = ""
    current_stage: str = "group"

    # Group stage stats
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    # Dynamic adjustments
    strength_multiplier: float = 1.0  # adjusted based on actual performance
    injury_impact: float = 0.0       # 0 to -0.2 for injuries

    # Qualified status
    is_eliminated: bool = False
    is_qualified: bool = False
    qualified_as: Literal["1st", "2nd", "3rd_best"] | None = None

    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against

    def effective_elo(self) -> float:
        """Elo adjusted for form and injuries."""
        return self.elo_rating * self.strength_multiplier + (self.injury_impact * 100)

    def update_from_result(self, result: MatchResult, is_home: bool) -> None:
        """Update team state based on a match result."""
        self.played += 1

        if is_home:
            self.goals_for += result.home_score
            self.goals_against += result.away_score
            if result.home_score > result.away_score:
                self.won += 1
                self.points += 3
            elif result.home_score == result.away_score:
                self.drawn += 1
                self.points += 1
            else:
                self.lost += 1
        else:
            self.goals_for += result.away_score
            self.goals_against += result.home_score
            if result.away_score > result.home_score:
                self.won += 1
                self.points += 3
            elif result.away_score == result.home_score:
                self.drawn += 1
                self.points += 1
            else:
                self.lost += 1

        # Adjust strength based on performance
        if result.winner == self.name:
            self.strength_multiplier = min(1.1, self.strength_multiplier + 0.01)
        else:
            self.strength_multiplier = max(0.9, self.strength_multiplier - 0.01)


# ── World State ────────────────────────────────────────────────────────────────

@dataclass
class WorldState:
    """
    The Agent's memory — tracks entire tournament state.

    This is what makes the Agent "stateful" across iterations.
    """
    tournament_name: str = "FIFA World Cup 2026"
    current_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # All teams and their states
    teams: dict[str, TeamState] = field(default_factory=dict)

    # Real match results (what happened)
    results: list[MatchResult] = field(default_factory=list)

    # Predicted vs actual (for evaluation)
    predictions_history: list[dict] = field(default_factory=list)

    # Current tournament stage
    current_stage: str = "group"

    # R32 bracket (populated after group stage)
    r32_bracket: dict[str, str] = field(default_factory=dict)  # match_id -> winner

    # Pending (not yet played) matches
    pending_matches: list[str] = field(default_factory=list)

    def add_team(self, name: str, elo: float = 1500, group: str = "") -> TeamState:
        """Add or update a team."""
        if name not in self.teams:
            self.teams[name] = TeamState(name=name, elo_rating=elo, group=group)
        return self.teams[name]

    def add_result(self, result: MatchResult) -> None:
        """Record a real match result and update team states."""
        self.results.append(result)

        # Update team states
        home_team = self.teams.get(result.home_team)
        away_team = self.teams.get(result.away_team)

        if home_team:
            home_team.update_from_result(result, is_home=True)
        if away_team:
            away_team.update_from_result(result, is_home=False)

        # Update bracket if knockout stage
        if result.stage in ("r32", "r16", "qf", "sf", "final"):
            if result.winner:
                self.r32_bracket[result.match_id] = result.winner

        # Remove from pending
        if result.match_id in self.pending_matches:
            self.pending_matches.remove(result.match_id)

    def get_standings(self, group: str) -> list[TeamState]:
        """Get sorted standings for a group."""
        group_teams = [t for t in self.teams.values() if t.group == group and not t.is_eliminated]
        return sorted(
            group_teams,
            key=lambda t: (
                -t.points,
                -t.goal_diff(),
                -t.goals_for,
                -t.elo_rating,
            )
        )

    def update_from_results(self) -> list[str]:
        """
        After receiving results, determine what predictions need updating.

        Returns list of reasons why predictions changed.
        """
        changes: list[str] = []

        # Group stage: check if standings changed significantly
        for team_name, team in self.teams.items():
            if team.strength_multiplier != 1.0:
                changes.append(
                    f"{team_name}: form adjusted to {team.strength_multiplier:.2f}x "
                    f"(after {team.won}W/{team.drawn}D/{team.lost}L)"
                )

        # Check for upsets
        for result in self.results[-5:]:  # last 5 results
            if result.winner:
                changes.append(
                    f"RESULT: {result.home_team} {result.home_score} - "
                    f"{result.away_score} {result.away_team} → {result.winner} wins"
                )

        return changes

    def should_repredict(self) -> bool:
        """
        Agent's decision function: should we regenerate predictions?

        Conditions:
        - New real results available
        - Bracket state changed
        - Team strengths significantly changed
        """
        if len(self.results) == 0:
            return True  # Initial prediction

        # Check if we have unprocessed results
        recent_results = [r for r in self.results if r.stage == self.current_stage]
        if len(recent_results) > len(self.predictions_history):
            return True

        # Check if any team form changed significantly
        for team in self.teams.values():
            if abs(team.strength_multiplier - 1.0) > 0.05:
                return True

        return False

    def to_dict(self) -> dict:
        return {
            "tournament": self.tournament_name,
            "current_date": self.current_date,
            "current_stage": self.current_stage,
            "teams": {
                name: {
                    "elo": team.elo_rating,
                    "effective_elo": team.effective_elo(),
                    "group": team.group,
                    "stage": team.current_stage,
                    "stats": {
                        "played": team.played,
                        "won": team.won,
                        "drawn": team.drawn,
                        "lost": team.lost,
                        "gf": team.goals_for,
                        "ga": team.goals_against,
                        "gd": team.goal_diff(),
                        "points": team.points,
                    },
                    "strength_multiplier": team.strength_multiplier,
                    "injury_impact": team.injury_impact,
                    "is_eliminated": team.is_eliminated,
                }
                for name, team in self.teams.items()
            },
            "results": [r.to_dict() for r in self.results],
            "bracket": self.r32_bracket,
            "pending": self.pending_matches,
        }

    @classmethod
    def from_dict(cls, d: dict) -> WorldState:
        """Restore WorldState from dict."""
        state = cls(
            tournament_name=d.get("tournament", "FIFA World Cup 2026"),
            current_date=d.get("current_date", ""),
            current_stage=d.get("current_stage", "group"),
        )

        for name, team_data in d.get("teams", {}).items():
            team = state.add_team(name, elo=team_data.get("elo", 1500), group=team_data.get("group", ""))
            stats = team_data.get("stats", {})
            team.played = stats.get("played", 0)
            team.won = stats.get("won", 0)
            team.drawn = stats.get("drawn", 0)
            team.lost = stats.get("lost", 0)
            team.goals_for = stats.get("gf", 0)
            team.goals_against = stats.get("ga", 0)
            team.points = stats.get("points", 0)
            team.strength_multiplier = team_data.get("strength_multiplier", 1.0)
            team.injury_impact = team_data.get("injury_impact", 0.0)
            team.is_eliminated = team_data.get("is_eliminated", False)

        for r_dict in d.get("results", []):
            result = MatchResult(
                match_id=r_dict["match_id"],
                home_team=r_dict["home_team"],
                away_team=r_dict["away_team"],
                home_score=r_dict["home_score"],
                away_score=r_dict["away_score"],
                stage=r_dict["stage"],
                kickoff=r_dict["kickoff"],
            )
            state.results.append(result)

        state.r32_bracket = d.get("bracket", {})
        state.pending_matches = d.get("pending", [])

        return state


# ── Persistence ────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STATE_FILE = DATA_DIR / "agent_state.json"


def save_world_state(state: WorldState) -> None:
    """Persist WorldState to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state.current_date = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_world_state() -> WorldState | None:
    """Load WorldState from disk, or None if not exists."""
    if not STATE_FILE.exists():
        return None
    try:
        d = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return WorldState.from_dict(d)
    except Exception:
        return None
