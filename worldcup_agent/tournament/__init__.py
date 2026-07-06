"""Tournament module — WC 2026 Rule Abstraction + Engine.

Four blocks:
  RULE      → rule.py       (immutable rule definitions)
  ENGINE    → r32_builder.py (R32 + third-place ranker)
  ENGINE    → knockout_simulator.py (full bracket simulation)
  PRESENTATION → NOT HERE (see frontend / page modules)
"""
from worldcup_agent.tournament.rule import (
    TournamentRule,
    GroupStanding,
    Stage,
    TIEBREAKERS,
)
from worldcup_agent.tournament.r32_builder import (
    R32Builder,
    ThirdPlaceRanker,
    ThirdPlaceRecord,
    ThirdPlaceRankingTrace,
    MatchTrace,
)
from worldcup_agent.tournament.knockout_simulator import (
    KnockoutSimulator,
    KnockoutMatch,
    KnockoutResult,
    EloProbModel,
)

__all__ = [
    # Rule
    "TournamentRule",
    "GroupStanding",
    "Stage",
    "TIEBREAKERS",
    # R32 Engine
    "R32Builder",
    "ThirdPlaceRanker",
    "ThirdPlaceRecord",
    "ThirdPlaceRankingTrace",
    "MatchTrace",
    # Knockout Engine
    "KnockoutSimulator",
    "KnockoutMatch",
    "KnockoutResult",
    "EloProbModel",
]
