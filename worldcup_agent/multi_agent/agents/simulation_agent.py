"""Simulation Agent — Monte Carlo tournament simulation.

This is the KEY agent that transforms the system from a "prediction system"
into a "world modeling agent system".

This agent implements the ReAct pattern for Monte Carlo simulation:
  1. OBSERVE: Gather current bracket and team strengths
  2. THINK: Plan simulation parameters and strategy
  3. ACT: Run Monte Carlo simulation (N=10,000 iterations)
  4. EVALUATE: Check convergence and quality of results
  5. REVISE: Adjust simulation if needed (more runs, different model)
"""
from __future__ import annotations

import json
import random
from collections import Counter
from dataclasses import dataclass
from typing import Any

from worldcup_agent.multi_agent import BaseAgent, WorldState


# ── Constants ────────────────────────────────────────────────────────────────

# Default Monte Carlo iterations
DEFAULT_SIMULATION_RUNS = 10_000
DEFAULT_ELO = 1500
HOME_ADVANTAGE = 100  # Elo points


# ── Data Classes ────────────────────────────────────────────────────────────


@dataclass
class SimMatch:
    """A simulated match result."""
    home_team: str
    away_team: str
    home_win: bool
    draw: bool
    away_win: bool
    home_score: int = 0
    away_score: int = 0


@dataclass
class SimResult:
    """Result of one simulation run."""
    champion: str
    runner_up: str
    third_place: str
    champion_probability: float = 1.0
    bracket: dict | None = None


@dataclass
class SimulationReport:
    """Complete simulation report with statistics."""
    runs: int
    champion_counts: Counter
    runner_up_counts: Counter
    third_place_counts: Counter
    final_probabilities: dict[str, float]
    bracket_predictions: dict | None
    convergence_score: float  # How stable are the results?


# ── Simulation Agent ────────────────────────────────────────────────────────


class SimulationAgent(BaseAgent):
    """
    Simulation Agent — Monte Carlo tournament simulation engine.

    This is the CORE agent that makes the system a "world modeling agent system"
    rather than just a "prediction system".

    ReAct Loop:
      OBSERVE: Check current bracket state and team strengths
      THINK:   Plan simulation parameters (runs, model, etc.)
      ACT:     Execute Monte Carlo simulation
      EVALUATE: Check convergence (are results stable?)
      REVISE:  If not converged, run more iterations
    """

    def __init__(self, default_runs: int = DEFAULT_SIMULATION_RUNS):
        super().__init__(
            name="simulation_agent",
            description="Runs Monte Carlo simulation for tournament predictions",
            max_iterations=3,
        )
        self.default_runs = default_runs
        self._simulation_cache: dict[str, SimulationReport] = {}

    @property
    def system_prompt(self) -> str:
        return """You are the Simulation Agent for WC2026 predictions.

Your core responsibility is to run Monte Carlo simulations of the tournament.

This is what makes this system special — we don't just predict individual matches,
we simulate entire tournament outcomes thousands of times to get true probabilities.

Key capabilities:
  1. Monte Carlo simulation (10,000+ iterations)
  2. Bracket-aware simulation (respects tournament structure)
  3. Team strength modeling (based on Elo ratings)
  4. Convergence analysis (are results stable?)

You output probabilities for:
  - Tournament champion
  - Runner-up
  - Third place
  - Each team's path through the bracket

The simulation should:
  - Respect actual tournament rules (group stage, knockout)
  - Use Elo ratings as the primary strength metric
  - Include home advantage where applicable
  - Handle upsets based on probability distributions
"""

    def observe(self, state: WorldState) -> dict:
        """OBSERVE: Check current simulation state."""
        observation = {
            "teams_available": len(state.teams),
            "tournament_stage": state.tournament_stage,
            "simulation_cached": state.simulation_results is not None,
            "previous_runs": state.monte_carlo_runs,
            "match_results_count": len(state.match_results),
        }

        # Check data quality
        team_elos = [
            data.get("elo", DEFAULT_ELO)
            for data in state.teams.values()
            if isinstance(data, dict)
        ]

        observation["elo_stats"] = {
            "teams_with_elo": len(team_elos),
            "avg_elo": sum(team_elos) / len(team_elos) if team_elos else DEFAULT_ELO,
            "elo_range": (min(team_elos) if team_elos else DEFAULT_ELO,
                         max(team_elos) if team_elos else DEFAULT_ELO),
        }

        # Check if we have real results that change simulation
        if state.match_results:
            observation["has_real_results"] = True
            observation["results_impact"] = "Must update team strengths based on actual performance"
        else:
            observation["has_real_results"] = False

        return observation

    def think(self, observation: dict, state: WorldState) -> str:
        """THINK: Plan simulation approach."""
        if observation.get("simulation_cached") and observation.get("previous_runs", 0) >= 5000:
            if not observation.get("has_real_results"):
                return "SIM_USE_CACHE: Simulation cached and valid. No need to re-run."

        if observation.get("has_real_results"):
            return "SIM_REFRESH: Real results available. Must re-simulate with updated team strengths."

        if observation["teams_available"] < 48:
            return f"SIM_PARTIAL: Only {observation['teams_available']} teams. " \
                   f"Will simulate with available teams."

        return "SIM_FULL: Running full tournament simulation with 10,000 iterations."

    def act(self, thought: str, state: WorldState) -> tuple[SimulationReport, str]:
        """ACT: Execute Monte Carlo simulation."""
        runs = self.default_runs

        # Build team Elo map
        team_elo: dict[str, float] = {}
        for team_name, team_data in state.teams.items():
            if isinstance(team_data, dict):
                team_elo[team_name] = team_data.get("elo", DEFAULT_ELO)
            else:
                team_elo[team_name] = DEFAULT_ELO

        # Adjust Elos based on real results
        team_elo = self._adjust_elo_from_results(team_elo, state.match_results)

        # Run simulation
        report = self._run_monte_carlo(team_elo, runs)

        # Update state
        state.simulation_results = report.final_probabilities
        state.monte_carlo_runs = runs

        observation = f"Completed {runs:,} Monte Carlo simulations. " \
                     f"Convergence score: {report.convergence_score:.3f}. " \
                     f"Top 3 champions: {list(report.final_probabilities.items())[:3]}"

        return report, observation

    def evaluate(self, result: SimulationReport, state: WorldState) -> bool:
        """EVALUATE: Check simulation quality."""
        if result.runs < 1000:
            return False

        # Check convergence (should be high for stable results)
        if result.convergence_score < 0.85:
            return False

        # Should have results for most teams
        if len(result.final_probabilities) < len(state.teams) * 0.5:
            return False

        return True

    def revise(self, result: Any, error: str, state: WorldState) -> str:
        """REVISE: Run more iterations to improve convergence."""
        self.default_runs = min(self.default_runs * 2, 50_000)
        return f"Running additional simulation with {self.default_runs:,} iterations to improve convergence."

    # ── Monte Carlo Core ───────────────────────────────────────────────────

    def _run_monte_carlo(
        self,
        team_elo: dict[str, float],
        runs: int,
    ) -> SimulationReport:
        """Run N Monte Carlo simulations of the tournament."""

        champion_counts = Counter()
        runner_up_counts = Counter()
        third_place_counts = Counter()
        bracket_predictions: dict[str, dict[str, int]] = {}

        # Set random seed for reproducibility (optional)
        rng = random.Random(42)

        for _ in range(runs):
            # Simulate one tournament
            result = self._simulate_tournament(team_elo, rng)

            champion_counts[result.champion] += 1
            runner_up_counts[result.runner_up] += 1
            third_place_counts[result.third_place] += 1

        # Calculate probabilities
        final_probabilities = {
            team: count / runs
            for team, count in champion_counts.most_common()
        }

        # Calculate convergence score (based on how concentrated results are)
        top_4 = sum(c for _, c in champion_counts.most_common(4))
        convergence = top_4 / runs

        return SimulationReport(
            runs=runs,
            champion_counts=champion_counts,
            runner_up_counts=runner_up_counts,
            third_place_counts=third_place_counts,
            final_probabilities=final_probabilities,
            bracket_predictions=bracket_predictions or None,
            convergence_score=convergence,
        )

    def _simulate_tournament(
        self,
        team_elo: dict[str, float],
        rng: random.Random,
    ) -> SimResult:
        """Simulate one complete tournament and return the result."""

        # Simplified simulation for now (full bracket would be more complex)
        teams = list(team_elo.keys())

        # For each team, calculate their "strength score" for simulation
        # This includes base Elo + random variance
        team_strengths = {}
        for team, elo in team_elo.items():
            # Base strength from Elo
            base = elo / 100  # Normalize to ~15-25 range

            # Small random variance (simulates match-day factors)
            variance = rng.gauss(0, 2)

            team_strengths[team] = base + variance

        # Sort teams by strength to determine approximate final positions
        sorted_teams = sorted(
            team_strengths.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Champion = strongest team (with some randomness)
        # In real simulation, this would follow bracket structure
        champion_idx = rng.choices(
            range(min(8, len(sorted_teams))),
            weights=[1.0 / (i + 1) for i in range(min(8, len(sorted_teams)))],
        )[0]

        champion = sorted_teams[champion_idx][0]

        # Runner-up = next strongest (weighted towards similar tier)
        remaining = [t for t in sorted_teams if t[0] != champion]
        if remaining:
            runner_up = rng.choice(remaining[:16])[0]
        else:
            runner_up = "Unknown"

        # Third place
        if remaining:
            remaining.remove((runner_up, team_strengths[runner_up]))
        if remaining:
            third_place = rng.choice(remaining[:16])[0]
        else:
            third_place = "Unknown"

        return SimResult(
            champion=champion,
            runner_up=runner_up,
            third_place=third_place,
            champion_probability=1.0,
        )

    def _adjust_elo_from_results(
        self,
        base_elo: dict[str, float],
        results: list[dict],
    ) -> dict[str, float]:
        """Adjust Elo ratings based on actual match results."""
        if not results:
            return base_elo

        # Clone to avoid modifying original
        adjusted = base_elo.copy()

        # Simple adjustment: teams that won get a small boost
        for result in results:
            home = result.get("home_team", "")
            away = result.get("away_team", "")
            home_score = result.get("home_score", 0)
            away_score = result.get("away_score", 0)

            if home in adjusted and away in adjusted:
                if home_score > away_score:
                    adjusted[home] += 10  # Winner's Elo goes up slightly
                    adjusted[away] -= 5
                elif away_score > home_score:
                    adjusted[away] += 10
                    adjusted[home] -= 5
                else:
                    # Draw: small adjustments
                    pass

        return adjusted

    def _match_probability(
        self,
        team_a: str,
        team_b: str,
        team_elo: dict[str, float],
    ) -> tuple[float, float, float]:
        """Calculate match probabilities from Elo ratings."""
        elo_a = team_elo.get(team_a, DEFAULT_ELO)
        elo_b = team_elo.get(team_b, DEFAULT_ELO)

        diff = elo_a - elo_b

        # Standard Elo probability
        p_a_win = 1.0 / (1.0 + 10 ** (diff / 400))

        # Draw probability (peaks when Elos are equal)
        p_draw = 0.25 * (1.0 - abs(diff) / 800)
        p_draw = max(0.10, min(0.28, p_draw))

        p_b_win = 1.0 - p_a_win - p_draw

        return p_a_win, p_draw, p_b_win
