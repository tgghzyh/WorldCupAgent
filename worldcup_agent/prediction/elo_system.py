"""Elo-based match prediction system.

Provides expected win/draw/lose probabilities from two Elo ratings.
Used by the agent to generate baseline match predictions.
"""
from __future__ import annotations

import math


class ELOSystem:
    """Lightweight Elo prediction engine for football match outcomes."""

    K_FACTOR = 32.0
    HOME_ADVANTAGE = 100   # Elo points equivalent of home advantage

    def expected_score(self, rating_a: float, rating_b: float) -> tuple[float, float, float]:
        """Return (win_prob_A, draw_prob, win_prob_B) for team A vs B.

        All three probabilities sum to 1.0.
        """
        # Home advantage: give team A a boost if playing at home
        r_a = rating_a + self.HOME_ADVANTAGE
        r_b = rating_b

        # Expected score using standard Elo formula
        # E(A wins) = 1 / (1 + 10^((R_b - R_a) / 400))
        win_a = 1.0 / (1.0 + 10.0 ** ((r_b - r_a) / 400.0))
        win_b = 1.0 / (1.0 + 10.0 ** ((r_a - r_b) / 400.0))

        # Draw probability: peaks when ratings are equal, decreases as gap widens
        draw_factor = 1.0 / (1.0 + 0.009 * abs(r_a - r_b))
        draw_prob = 0.27 * draw_factor

        # Normalise so win_a + draw + win_b = 1
        total = win_a + draw_prob + win_b
        win_a /= total
        win_b /= total
        draw_prob /= total

        return win_a, draw_prob, win_b

    def expected_goals(self, rating_a: float, rating_b: float) -> tuple[float, float]:
        """Return (expected_goals_A, expected_goals_B) for a neutral-ground match."""
        rating_diff = rating_a - rating_b
        base_home = 1.35
        diff_factor = rating_diff / 100.0 * 0.15
        lambda_home = max(0.3, base_home + diff_factor)
        lambda_away = max(0.3, base_home - diff_factor)
        return lambda_home, lambda_away
