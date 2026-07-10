"""Deterministic match probabilities grounded in extracted team intelligence."""

from __future__ import annotations

import math
from typing import Any


MODEL_VERSION = "team_intelligence_probability_v1"


def build_match_probability(
    home_team: str,
    away_team: str,
    home_profile: dict[str, Any],
    away_profile: dict[str, Any],
    home_intelligence: dict[str, Any] | None,
    away_intelligence: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a reproducible W/D/L baseline for the prediction LLM to assess."""

    home_signals = _team_signals(home_profile, home_intelligence or {})
    away_signals = _team_signals(away_profile, away_intelligence or {})

    home_rating = _weighted_rating(home_signals)
    away_rating = _weighted_rating(away_signals)
    home_advantage = 0.10
    edge = max(-2.2, min(2.2, (home_rating - away_rating) * 2.05 + home_advantage))
    draw_probability = max(0.16, min(0.29, 0.26 - min(abs(edge), 1.5) * 0.055))
    home_non_draw = 1 / (1 + math.exp(-edge))
    home_probability = home_non_draw * (1 - draw_probability)
    away_probability = 1 - home_probability - draw_probability
    home_probability, draw_probability, away_probability = _normalize(
        home_probability,
        draw_probability,
        away_probability,
    )

    return {
        "model_version": MODEL_VERSION,
        "method": "LLM team-intelligence feature score + Elo/ranking calibration + scheduled-home adjustment",
        "home_team": home_team,
        "away_team": away_team,
        "home_win_prob": round(home_probability, 4),
        "draw_prob": round(draw_probability, 4),
        "away_win_prob": round(away_probability, 4),
        "home_rating": round(home_rating, 4),
        "away_rating": round(away_rating, 4),
        "home_advantage": home_advantage,
        "feature_inputs": {
            "home": home_signals,
            "away": away_signals,
        },
    }


def _team_signals(profile: dict[str, Any], intelligence: dict[str, Any]) -> dict[str, float]:
    rank = _number(profile.get("fifa_rank"), 80)
    elo = _number(profile.get("elo"), 1500)
    components = intelligence.get("components", {}) if isinstance(intelligence, dict) else {}
    overall = _number(intelligence.get("overall_strength"), 50)
    return {
        "overall_strength": _score(overall),
        "attack": _score(_number(components.get("attack"), overall)),
        "defense": _score(_number(components.get("defense"), overall)),
        "midfield": _score(_number(components.get("midfield"), overall)),
        "squad_depth": _score(_number(components.get("squad_depth"), overall)),
        "coach_tactics": _score(_number(components.get("coach_tactics"), 50)),
        "tournament_experience": _score(_number(components.get("tournament_experience"), 50)),
        "form": _score(_number(components.get("form"), overall)),
        "elo": max(0.0, min(1.0, (elo - 1200) / 1000)),
        "ranking": max(0.0, min(1.0, (85 - rank) / 84)),
    }


def _weighted_rating(signals: dict[str, float]) -> float:
    feature_rating = (
        signals["overall_strength"] * 0.24
        + signals["attack"] * 0.11
        + signals["defense"] * 0.11
        + signals["midfield"] * 0.09
        + signals["squad_depth"] * 0.08
        + signals["coach_tactics"] * 0.09
        + signals["tournament_experience"] * 0.08
        + signals["form"] * 0.12
    )
    return max(0.0, min(1.0, feature_rating * 0.74 + signals["elo"] * 0.18 + signals["ranking"] * 0.08))


def _normalize(home: float, draw: float, away: float) -> tuple[float, float, float]:
    values = [max(0.01, home), max(0.01, draw), max(0.01, away)]
    total = sum(values)
    return tuple(value / total for value in values)  # type: ignore[return-value]


def _number(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _score(value: float) -> float:
    return max(0.0, min(1.0, value / 100))
