"""Explainer Agent — generates natural language explanations.

This agent implements the ReAct pattern for explanation generation:
  1. OBSERVE: Gather prediction and analysis data
  2. THINK: Plan explanation structure
  3. ACT: Generate explanations
  4. EVALUATE: Check explanation quality
  5. REVISE: Improve clarity if needed
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from worldcup_agent.multi_agent import BaseAgent, WorldState


class ExplainerAgent(BaseAgent):
    """
    Explainer Agent — generates natural language explanations.

    Transforms prediction probabilities into human-understandable narratives.

    ReAct Loop:
      OBSERVE: Gather prediction data and analysis
      THINK:   Plan explanation structure
      ACT:     Generate explanations
      EVALUATE: Check clarity and accuracy
      REVISE:  Improve if needed
    """

    def __init__(self):
        super().__init__(
            name="explainer_agent",
            description="Generates natural language explanations for predictions",
            max_iterations=2,
        )

    @property
    def system_prompt(self) -> str:
        return """You are the Explainer Agent for WC2026 predictions.

Your responsibilities:
  1. Generate natural language explanations for predictions
  2. Make complex probabilities accessible to general audiences
  3. Identify and explain key factors in predictions
  4. Highlight interesting aspects (upsets, close matches, etc.)

You should:
  - Use simple, clear language
  - Include specific numbers and evidence
  - Acknowledge uncertainty honestly
  - Highlight what makes each prediction interesting

Output formats:
  - Short summary (2-3 sentences)
  - Key factors (bullet points)
  - Narrative explanation (paragraph)
"""


# ── Explanation Types ────────────────────────────────────────────────────────


@dataclass
class PredictionExplanation:
    """Complete explanation for a prediction."""
    match_id: str
    short_summary: str = ""
    key_factors: list[dict] = field(default_factory=list)
    narrative: str = ""
    upset_risk: str | None = None
    confidence_explanation: str = ""


# ── ReAct Implementation ───────────────────────────────────────────────────


    def observe(self, state: WorldState) -> dict:
        """OBSERVE: Gather prediction and analysis data."""
        observation = {
            "predictions_available": len(state.predictions),
            "simulation_available": state.simulation_results is not None,
            "teams_available": len(state.teams),
        }

        # Sample predictions for explanation
        if state.predictions:
            sample_preds = list(state.predictions.items())[:3]
            observation["sample_predictions"] = [
                {
                    "id": k,
                    "home_win": v.get("outcome", {}).get("home_win", 0),
                    "away_win": v.get("outcome", {}).get("away_win", 0),
                }
                for k, v in sample_preds
            ]

        # Sample simulation results
        if state.simulation_results:
            top_champs = sorted(
                state.simulation_results.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3]
            observation["top_champions"] = top_champs

        return observation

    def think(self, observation: dict, state: WorldState) -> str:
        """THINK: Plan explanation approach."""
        if observation.get("simulation_available"):
            return "EXPLAIN_TOURNAMENT: Will generate tournament-level explanations with simulation data."

        if observation.get("predictions_available") > 0:
            return "EXPLAIN_MATCHES: Will generate match-level explanations for predictions."

        return "EXPLAIN_BASELINE: Will provide general explanation of prediction methodology."

    def act(self, thought: str, state: WorldState) -> tuple[dict, str]:
        """ACT: Generate explanations."""
        explanations = {
            "match_explanations": [],
            "tournament_explanation": None,
            "key_insights": [],
        }

        # Generate match explanations
        for match_id, pred in list(state.predictions.items())[:10]:
            if isinstance(pred, dict):
                outcome = pred.get("outcome", {})
                if outcome:
                    home = pred.get("home_team", "Home")
                    away = pred.get("away_team", "Away")
                    home_win = outcome.get("home_win", 0.33)
                    away_win = outcome.get("away_win", 0.33)
                    draw = outcome.get("draw", 0.33)

                    # Generate short summary
                    if home_win > away_win:
                        favorite = home
                        underdog = away
                        prob = home_win
                    else:
                        favorite = away
                        underdog = home
                        prob = away_win

                    summary = f"{favorite} has a {prob:.0%} chance of winning against {underdog}."

                    # Generate key factors
                    factors = pred.get("factors", [])
                    if not factors:
                        factors = [
                            {"name": "ELO Rating", "contribution_pct": 0.45},
                            {"name": "Recent Form", "contribution_pct": 0.30},
                            {"name": "Home Advantage", "contribution_pct": 0.15},
                        ]

                    # Check for upset potential
                    upset_risk = None
                    if prob < 0.6 and away_win > 0.25:
                        upset_risk = f"Upset alert: {underdog} has a {away_win:.0%} chance of winning."

                    explanations["match_explanations"].append({
                        "match_id": match_id,
                        "home_team": home,
                        "away_team": away,
                        "short_summary": summary,
                        "key_factors": factors[:3],
                        "upset_risk": upset_risk,
                        "confidence": self._explain_confidence(outcome),
                    })

        # Generate tournament explanation
        if state.simulation_results:
            top_3 = sorted(
                state.simulation_results.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3]

            explanations["tournament_explanation"] = {
                "champion_favorites": [
                    {"team": team, "probability": f"{prob:.1%}"}
                    for team, prob in top_3
                ],
                "narrative": self._generate_tournament_narrative(state.simulation_results),
            }

            # Key insights
            explanations["key_insights"] = self._generate_key_insights(state)

        observation = f"Generated {len(explanations['match_explanations'])} match explanations. " \
                     f"Tournament explanation: {'generated' if explanations['tournament_explanation'] else 'pending'}."

        return explanations, observation

    def evaluate(self, result: dict, state: WorldState) -> bool:
        """EVALUATE: Check explanation quality."""
        if not result.get("match_explanations") and not result.get("tournament_explanation"):
            return False

        return True

    def revise(self, result: Any, error: str, state: WorldState) -> str:
        """REVISE: Generate more detailed explanations."""
        return "Adding more context and examples to improve clarity."

    # ── Helper Methods ───────────────────────────────────────────────────

    def _explain_confidence(self, outcome: dict) -> str:
        """Explain confidence level."""
        home_win = outcome.get("home_win", 0.33)
        away_win = outcome.get("away_win", 0.33)
        draw = outcome.get("draw", 0.33)

        spread = max(home_win, draw, away_win) - min(home_win, draw, away_win)

        if spread > 0.45:
            return "High confidence — clear favorite"
        elif spread > 0.20:
            return "Medium confidence — competitive match"
        else:
            return "Low confidence — very uncertain outcome"

    def _generate_tournament_narrative(self, sim_results: dict) -> str:
        """Generate tournament-level narrative."""
        top_3 = sorted(sim_results.items(), key=lambda x: x[1], reverse=True)[:3]

        if not top_3:
            return "Not enough data for tournament prediction."

        champion = top_3[0][0]
        champ_prob = top_3[0][1]

        narrative = f"Based on 10,000 Monte Carlo simulations, {champion} is the most likely " \
                   f"champion with a {champ_prob:.1%} probability"

        if len(top_3) > 1:
            second = top_3[1][0]
            second_prob = top_3[1][1]
            narrative += f". {second} follows with {second_prob:.1%}"

        if champ_prob > 0.3:
            narrative += ". This is a relatively clear favorite."
        elif champ_prob > 0.15:
            narrative += ". It's a competitive field with multiple contenders."
        else:
            narrative += ". The tournament is wide open with no clear favorite."

        return narrative

    def _generate_key_insights(self, state: WorldState) -> list[str]:
        """Generate key insights from simulation."""
        insights = []

        if state.simulation_results:
            # Find dark horses (teams with decent probability but not top tier)
            sorted_results = sorted(
                state.simulation_results.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            if len(sorted_results) > 5:
                dark_horse_candidates = [
                    t for t, p in sorted_results[5:15] if p > 0.02
                ]
                if dark_horse_candidates:
                    insights.append(
                        f"Dark horse teams to watch: {', '.join(dark_horse_candidates[:3])}"
                    )

            # Find competitive groups
            if state.teams:
                # Simplified: just note teams with similar Elos
                group_analysis = {}
                for team, data in list(state.teams.items())[:8]:
                    if isinstance(data, dict):
                        elo = data.get("elo", 1500)
                        tier = int((elo - 1500) / 50)
                        if tier not in group_analysis:
                            group_analysis[tier] = []
                        group_analysis[tier].append(team)

                for tier, teams in group_analysis.items():
                    if len(teams) >= 2:
                        insights.append(
                            f"Tier {tier} teams: {', '.join(teams[:2])} should have competitive matches"
                        )

        return insights
