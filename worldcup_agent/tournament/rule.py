"""FIFA World Cup 2026 — Tournament Rule Abstraction.

Block: RULE
No Engine, No Trace, No Presentation here.
Only immutable rule definitions and data structures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ── Stage definitions ──────────────────────────────────────────────────────────

GROUP_STAGES = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
KNOCKOUT_ORDER = ["round_of_32", "round_of_16", "quarter_final", "semi_final", "third_place", "final"]
KNOCKOUT_SIZES = {
    "round_of_32": 32,
    "round_of_16": 16,
    "quarter_final": 8,
    "semi_final": 4,
    "third_place": 2,
    "final": 2,
}


@dataclass(frozen=True)
class Stage:
    """Immutable tournament stage definition."""
    name: str                          # e.g. "round_of_32"
    team_count: int                    # teams entering this stage
    matches: int                       # games played in this stage
    description: str = ""

    @classmethod
    def all(cls) -> list[Stage]:
        return [
            cls("round_of_32", 32, 16, "48→32 → 16 matches"),
            cls("round_of_16", 16, 8,  "16 teams → 8 matches"),
            cls("quarter_final", 8,  4,  "8 teams → 4 matches"),
            cls("semi_final",   4,  2,  "4 teams → 2 matches"),
            cls("third_place",  2,  1,  "Losers of semi-finals"),
            cls("final",        2,  1,  "Champion decided"),
        ]


# ── Group & tiebreaker ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Tiebreaker:
    """
    Group ranking tiebreaker, in application order.

    2026 FIFA World Cup Official Rules (IMPORTANT: NEW ORDER!)
    The first three tiebreakers compare HEAD-TO-HEAD results only,
    NOT overall statistics. This is a key change from previous tournaments.
    """
    key: str
    direction: Literal["desc", "asc"]
    label: str
    is_head_to_head: bool = False  # Flag for head-to-head tiebreakers

    def apply(self, a: "GroupStanding", b: "GroupStanding") -> int:
        va = getattr(a, self.key, 0)
        vb = getattr(b, self.key, 0)
        if va != vb:
            return (vb - va) if self.direction == "desc" else (va - vb)
        return 0


# 2026 Official Tiebreaker Sequence
TIEBREAKERS = [
    # Phase 1: Head-to-head comparison (NEW in 2026)
    Tiebreaker("h2h_points",      "desc", "Points in head-to-head matches", is_head_to_head=True),
    Tiebreaker("h2h_goal_diff",  "desc", "Goal difference in head-to-head", is_head_to_head=True),
    Tiebreaker("h2h_goals",       "desc", "Goals scored in head-to-head", is_head_to_head=True),

    # Phase 2: Reapply head-to-head to remaining tied teams
    # (handled by Engine by re-running phase 1)

    # Phase 3: Overall statistics
    Tiebreaker("goal_diff",      "desc", "Higher goal difference"),
    Tiebreaker("goals_scored",   "desc", "More goals scored"),

    # Phase 4: Fair play
    Tiebreaker("fair_play",      "desc", "Higher fair play points"),

    # Phase 5: Drawing of lots (FIFA ranking as proxy)
    Tiebreaker("fifa_rank",      "asc",  "Better FIFA ranking (lower number is better)"),
]


# ── Core rule container ────────────────────────────────────────────────────────

@dataclass
class TournamentRule:
    """
    Immutable configuration for WC 2026 tournament structure.

    Block: RULE — does NOT contain any Engine or Trace logic.
    """
    year: int = 2026
    teams: int = 48
    groups: int = 12
    group_size: int = 4
    qualifiers_per_group: int = 2
    third_place_advancers: int = 8
    knockout_order: tuple[str, ...] = field(
        default_factory=lambda: tuple(KNOCKOUT_ORDER)
    )
    knockout_sizes: dict[str, int] = field(
        default_factory=lambda: dict(KNOCKOUT_SIZES)
    )

    # Fixed runner-up derby matchups (Match numbers, public schedule info)
    FIXED_RUNNER_UP_PAIRS: tuple[tuple[str, str], ...] = field(default_factory=lambda: (
        ("2A", "2B"),  # M73
        ("1F", "2C"),  # M75
        ("1C", "2F"),  # M76
        ("2E", "2I"),  # M78
        ("2K", "2L"),  # M83
        ("1H", "2J"),  # M84
        ("1J", "2H"),  # M86
        ("2D", "2G"),  # M88
    ))

    # Allowed third-place opponent groups for each champion slot (constraint 2)
    CHAMPION_THIRD_SLOTS: dict[str, list[str]] = field(default_factory=lambda: {
        "1A": ["C", "E", "F", "H", "I"],
        "1B": ["E", "F", "G", "I", "J"],
        "1D": ["B", "E", "F", "I", "J"],
        "1E": ["A", "B", "C", "D", "F"],
        "1G": ["A", "E", "H", "I", "J"],
        "1I": ["C", "D", "F", "G", "H"],
        "1K": ["D", "E", "I", "J", "L"],
        "1L": ["E", "H", "I", "J", "K"],
    })

    @classmethod
    def wc2026(cls) -> "TournamentRule":
        return cls()

    def total_matches(self) -> int:
        """
        Total matches in 2026 World Cup: 104

        Breakdown:
        - Group Stage: 12 groups × 6 matches per group = 72 matches
        - Round of 32: 16 matches (32 → 16)
        - Round of 16: 8 matches (16 → 8)
        - Quarter-finals: 4 matches (8 → 4)
        - Semi-finals: 2 matches (4 → 2)
        - Third place: 1 match
        - Final: 1 match
        """
        return 72 + 16 + 8 + 4 + 2 + 1 + 1  # 104 matches


# ── Group standing (input to Engine) ───────────────────────────────────────────

@dataclass
class GroupStanding:
    """
    Group ranking record for one team.

    Block: RULE — this is pure data, no logic.

    2026 Official Fields:
    - Standard stats (played, won, drawn, lost, goals_for, goals_against, etc.)
    - Head-to-head stats (h2h_points, h2h_goal_diff, h2h_goals) for tiebreaking
    """
    group: str              # "A".."L"
    rank: int               # 1=winner, 2=runner-up, 3=third, 4=fourth
    team: str               # team name
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_diff: int = 0
    points: int = 0
    fair_play: int = 0      # Fair play points (higher is better)
    fifa_rank: int = 0      # FIFA world ranking (lower is better)

    # 2026 NEW: Head-to-head tiebreaker fields
    h2h_points: int = 0     # Points from head-to-head matches
    h2h_goal_diff: int = 0  # Goal difference from head-to-head matches
    h2h_goals: int = 0     # Goals scored in head-to-head matches
    h2h_matches: int = 0    # Number of head-to-head matches played

    def __post_init__(self):
        if self.goal_diff == 0 and (self.goals_for or self.goals_against):
            object.__setattr__(self, "goal_diff", self.goals_for - self.goals_against)
