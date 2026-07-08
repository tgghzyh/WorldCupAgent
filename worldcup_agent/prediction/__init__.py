"""Prediction module for WC2026.

Exports core prediction types and utilities.
"""
from worldcup_agent.prediction.prediction_schema import (
    PredictionSnapshot,
    MatchPrediction,
    OutcomeProbability,
    FactorAttribution,
    save_snapshot,
    load_snapshot,
    list_snapshots,
    compare_snapshots,
    get_latest_snapshot,
    promote_to_latest,
    SNAPSHOT_DIR,
)
from worldcup_agent.prediction.elo_system import ELOSystem
from worldcup_agent.prediction.world_state import WorldState, MatchResult, TeamState
from worldcup_agent.prediction.observer import TournamentObserver, ObservationSet, Observation

__all__ = [
    "PredictionSnapshot",
    "MatchPrediction",
    "OutcomeProbability",
    "FactorAttribution",
    "save_snapshot",
    "load_snapshot",
    "list_snapshots",
    "compare_snapshots",
    "get_latest_snapshot",
    "promote_to_latest",
    "SNAPSHOT_DIR",
    "ELOSystem",
    "WorldState",
    "MatchResult",
    "TeamState",
    "TournamentObserver",
    "ObservationSet",
    "Observation",
]
