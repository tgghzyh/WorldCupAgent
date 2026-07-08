"""Concrete agents used by the WC2026 multi-agent pipeline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from worldcup_agent.data_layer import DataForAgentError, load_dataset, load_processed_index
from worldcup_agent.multi_agent.core import BaseAgent, WorldState


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LATEST_SNAPSHOT = PROJECT_ROOT / "data" / "snapshots" / "latest.json"


def _load_latest_snapshot() -> dict[str, Any]:
    if not LATEST_SNAPSHOT.exists():
        return {}
    with LATEST_SNAPSHOT.open("r", encoding="utf-8") as f:
        return json.load(f)


def _teams_from_snapshot(snapshot: dict[str, Any]) -> dict[str, dict]:
    teams: dict[str, dict] = {}
    for group_name, group in snapshot.get("group_predictions", {}).items():
        for row in group.get("standings", []):
            team = row.get("team")
            if not team:
                continue
            teams[team] = {
                "name": team,
                "group": group_name,
                "points": row.get("points", 0),
                "goal_diff": row.get("goal_diff", 0),
                "source": "prediction_snapshot",
            }
    return teams


def _parse_snapshot_probability(raw: Any, simulations: int = 0) -> float | None:
    try:
        if isinstance(raw, (int, float)):
            value = float(raw)
            if value > 1 and simulations > 0:
                return value / simulations
            return value / 100 if value > 1 else value
        if isinstance(raw, str) and "(" in raw and raw.endswith("%)"):
            return float(raw.rsplit("(", 1)[1].rstrip("%)")) / 100
        if isinstance(raw, str) and raw.endswith("%"):
            return float(raw.rstrip("%")) / 100
    except ValueError:
        return None
    return None


def _is_degenerate_distribution(probabilities: dict[str, float]) -> bool:
    if len(probabilities) < 2:
        return True
    values = list(probabilities.values())
    return max(values) >= 0.995 and sum(1 for value in values if value > 0.001) <= 1


def _snapshot_champion_probabilities(snapshot: dict[str, Any]) -> dict[str, float]:
    probabilities: dict[str, float] = {}
    simulations = int(snapshot.get("monte_carlo_simulations") or 0)
    for team, raw in snapshot.get("champion_probabilities", {}).items():
        value = _parse_snapshot_probability(raw, simulations)
        if value is None:
            continue
        probabilities[team] = max(0.0, min(1.0, value))
    return probabilities


def _calibrated_probabilities_from_strengths(
    strengths: dict[str, float],
    champion: str | None = None,
) -> dict[str, float]:
    if not strengths:
        return {}

    temperature = 8.0
    adjusted = {
        team: max(0.0, score) + (0.16 if champion and team == champion else 0.0)
        for team, score in strengths.items()
    }
    weights = {team: math.exp(score * temperature) for team, score in adjusted.items()}
    total = sum(weights.values()) or 1.0
    return {team: weight / total for team, weight in weights.items()}


class DataAgent(BaseAgent):
    """Loads normalized initial data from DataForAgent into the shared state."""

    def __init__(self) -> None:
        super().__init__("data_agent", "Loads initial World Cup datasets")

    @property
    def system_prompt(self) -> str:
        return "Load DataForAgent normalized datasets and populate WorldState."

    def observe(self, state: WorldState) -> dict:
        return {
            "teams_loaded": len(state.teams),
            "has_results": len(state.match_results) > 0,
            "snapshot_exists": LATEST_SNAPSHOT.exists(),
        }

    def think(self, observation: dict, state: WorldState) -> str:
        return "Load DataForAgent processed datasets and the canonical prediction snapshot."

    def act(self, thought: str, state: WorldState) -> tuple[Any, str]:
        try:
            index = load_processed_index()
            worldcup = load_dataset("worldcup")
            leagues = load_dataset("leagues")
            squad = load_dataset("wc2026_squad")
        except DataForAgentError as exc:
            state.errors.append(str(exc))
            raise

        snapshot = _load_latest_snapshot()
        state.teams = _teams_from_snapshot(snapshot)
        state.match_results = worldcup.get("matches", [])

        if not state.teams:
            state.warnings.append("No teams found in canonical snapshot; team state is empty.")

        squad_stats = squad.get("stats", {})
        if squad_stats.get("teams") != len(state.teams):
            state.warnings.append(
                "DataForAgent squad count and snapshot team count differ "
                f"({squad_stats.get('teams')} vs {len(state.teams)})."
            )

        state.elo_last_updated = index.get("generated_at")
        state.odds_last_updated = snapshot.get("snapshot_time")
        state.injury_last_updated = None
        state.predictions["data_sources"] = {
            "dataforagent_generated_at": index.get("generated_at"),
            "datasets": sorted(index.get("datasets", {}).keys()),
            "worldcup_matches": worldcup.get("metadata", {}).get("totals", {}).get("matches"),
            "league_matches": leagues.get("metadata", {}).get("total_matches")
            or len(leagues.get("matches", [])),
            "squad_stats": squad_stats,
            "snapshot_time": snapshot.get("snapshot_time"),
        }

        return state.predictions["data_sources"], (
            f"Loaded {len(state.teams)} teams, {len(state.match_results)} historical matches, "
            f"{squad_stats.get('total_players', 0)} squad players"
        )

    def evaluate(self, result: Any, state: WorldState) -> bool:
        return len(state.teams) > 0 and len(state.match_results) > 0


class AnalysisAgent(BaseAgent):
    """Creates lightweight team strength scores from the shared state."""

    def __init__(self) -> None:
        super().__init__("analysis_agent", "Analyzes team strengths")

    @property
    def system_prompt(self) -> str:
        return "Analyze team strengths using WorldState evidence."

    def observe(self, state: WorldState) -> dict:
        return {"teams": len(state.teams), "has_data_sources": "data_sources" in state.predictions}

    def think(self, observation: dict, state: WorldState) -> str:
        return "Combine group results and champion probabilities into a normalized strength score."

    def act(self, thought: str, state: WorldState) -> tuple[Any, str]:
        snapshot = _load_latest_snapshot()
        champion_probabilities = _snapshot_champion_probabilities(snapshot)
        if _is_degenerate_distribution(champion_probabilities):
            champion_probabilities = {}

        scores: dict[str, float] = {}
        for team, data in state.teams.items():
            points_component = min(float(data.get("points", 0)) / 9.0, 1.0) * 0.35
            goal_component = max(min(float(data.get("goal_diff", 0)) / 8.0, 1.0), -1.0) * 0.15
            champion_component = champion_probabilities.get(team, 0.0) * 0.50
            score = max(0.0, min(1.0, points_component + goal_component + champion_component))
            data["strength_score"] = round(score, 4)
            scores[team] = data["strength_score"]

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        state.predictions["team_strengths"] = dict(ranked)
        return ranked[:10], f"Ranked {len(ranked)} teams by strength"

    def evaluate(self, result: Any, state: WorldState) -> bool:
        return bool(state.predictions.get("team_strengths"))


class SimulationAgent(BaseAgent):
    """Builds a tournament-level prediction summary."""

    def __init__(self, default_runs: int = 10_000) -> None:
        super().__init__("simulation_agent", "Runs tournament simulation summary")
        self.default_runs = default_runs

    @property
    def system_prompt(self) -> str:
        return "Estimate tournament outcomes from analyzed team strengths."

    def observe(self, state: WorldState) -> dict:
        return {"strengths": len(state.predictions.get("team_strengths", {}))}

    def think(self, observation: dict, state: WorldState) -> str:
        return "Use canonical snapshot probabilities when present; otherwise derive a softmax fallback."

    def act(self, thought: str, state: WorldState) -> tuple[Any, str]:
        snapshot = _load_latest_snapshot()
        champion_probabilities = _snapshot_champion_probabilities(snapshot)
        if not champion_probabilities or _is_degenerate_distribution(champion_probabilities):
            strengths = state.predictions.get("team_strengths", {})
            champion_probabilities = _calibrated_probabilities_from_strengths(
                strengths,
                champion=snapshot.get("champion"),
            )

        champion = max(champion_probabilities, key=champion_probabilities.get)
        result = {
            "predicted_champion": champion,
            "champion_probability": round(champion_probabilities[champion], 4),
            "champion_probabilities": {
                team: round(prob, 4)
                for team, prob in sorted(
                    champion_probabilities.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            },
            "source_snapshot": snapshot.get("prediction_version"),
        }

        state.simulation_results = result
        state.monte_carlo_runs = int(snapshot.get("monte_carlo_simulations") or self.default_runs)
        state.predictions["tournament"] = result
        return result, f"Predicted champion: {champion}"

    def evaluate(self, result: Any, state: WorldState) -> bool:
        return isinstance(result, dict) and bool(result.get("predicted_champion"))


class ReflectionAgent(BaseAgent):
    """Checks the consistency of the current shared state."""

    def __init__(self) -> None:
        super().__init__("reflection_agent", "Validates pipeline consistency")

    @property
    def system_prompt(self) -> str:
        return "Review data and prediction consistency."

    def observe(self, state: WorldState) -> dict:
        return {
            "teams": len(state.teams),
            "warnings": len(state.warnings),
            "errors": len(state.errors),
            "has_simulation": state.simulation_results is not None,
        }

    def think(self, observation: dict, state: WorldState) -> str:
        return "Check minimum viable tournament state before explanation and quality gates."

    def act(self, thought: str, state: WorldState) -> tuple[Any, str]:
        checks = {
            "has_48_teams": len(state.teams) == 48,
            "has_historical_matches": len(state.match_results) > 0,
            "has_simulation": state.simulation_results is not None,
            "has_dataforagent_sources": "data_sources" in state.predictions,
        }
        for name, ok in checks.items():
            if not ok:
                state.warnings.append(f"Reflection check failed: {name}")
        state.predictions["reflection_checks"] = checks
        return checks, f"{sum(checks.values())}/{len(checks)} checks passed"

    def evaluate(self, result: Any, state: WorldState) -> bool:
        return all(result.values())


class ExplainerAgent(BaseAgent):
    """Generates compact explanation text for the current tournament prediction."""

    def __init__(self) -> None:
        super().__init__("explainer_agent", "Explains predictions")

    @property
    def system_prompt(self) -> str:
        return "Explain tournament predictions from model evidence."

    def observe(self, state: WorldState) -> dict:
        return {"has_tournament_prediction": "tournament" in state.predictions}

    def think(self, observation: dict, state: WorldState) -> str:
        return "Summarize the champion pick and cite DataForAgent coverage."

    def act(self, thought: str, state: WorldState) -> tuple[Any, str]:
        tournament = state.predictions.get("tournament", {})
        sources = state.predictions.get("data_sources", {})
        champion = tournament.get("predicted_champion", "Unknown")
        probability = tournament.get("champion_probability", 0)
        explanation = (
            f"{champion} is the current champion pick at {probability:.1%}. "
            "The run used DataForAgent processed coverage "
            f"({sources.get('worldcup_matches')} historical World Cup matches, "
            f"{sources.get('squad_stats', {}).get('total_players')} squad players) "
            "and the canonical prediction snapshot."
        )
        state.predictions["explanation"] = explanation
        return explanation, "Generated tournament explanation"

    def evaluate(self, result: Any, state: WorldState) -> bool:
        return isinstance(result, str) and len(result) > 20


class QualityAgent(BaseAgent):
    """Final quality gate for the multi-agent pipeline."""

    def __init__(self) -> None:
        super().__init__("quality_agent", "Performs final quality checks")

    @property
    def system_prompt(self) -> str:
        return "Evaluate output completeness and known warnings."

    def observe(self, state: WorldState) -> dict:
        return {
            "teams": len(state.teams),
            "prediction_keys": sorted(state.predictions.keys()),
            "warnings": state.warnings,
            "errors": state.errors,
        }

    def think(self, observation: dict, state: WorldState) -> str:
        return "Score the pipeline on data coverage, prediction availability, and explanation availability."

    def act(self, thought: str, state: WorldState) -> tuple[Any, str]:
        checks = {
            "teams_loaded": len(state.teams) >= 48,
            "data_sources_loaded": "data_sources" in state.predictions,
            "tournament_prediction": "tournament" in state.predictions,
            "explanation": "explanation" in state.predictions,
            "no_errors": len(state.errors) == 0,
        }
        score = sum(checks.values()) / len(checks)
        result = {"score": round(score, 4), "checks": checks}
        state.predictions["quality"] = result
        if score < 0.8:
            state.warnings.append(f"Quality score below target: {score:.0%}")
        return result, f"Quality score: {score:.0%}"

    def evaluate(self, result: Any, state: WorldState) -> bool:
        return result.get("score", 0) >= 0.8
