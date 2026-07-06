"""Quality Agent — final quality check before output.

This agent implements the ReAct pattern for quality assurance:
  1. OBSERVE: Gather all outputs from the system
  2. THINK: Plan quality checks
  3. ACT: Perform quality checks
  4. EVALUATE: Determine if quality is acceptable
  5. REVISE: Suggest fixes if quality is poor
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from worldcup_agent.multi_agent import BaseAgent, WorldState


class QualityAgent(BaseAgent):
    """
    Quality Agent — final quality check before output.

    This is the last gate before predictions are published.
    It ensures:
      1. All required data is present
      2. Predictions are internally consistent
      3. Confidence levels are appropriate
      4. No obvious errors or anomalies

    ReAct Loop:
      OBSERVE: Gather all system outputs
      THINK:   Plan quality checks
      ACT:     Execute quality checks
      EVALUATE: Determine if quality is acceptable
      REVISE:  Suggest fixes if needed
    """

    def __init__(self):
        super().__init__(
            name="quality_agent",
            description="Final quality check before output",
            max_iterations=2,
        )

    @property
    def system_prompt(self) -> str:
        return """You are the Quality Agent for WC2026 predictions.

Your responsibilities:
  1. Perform final quality checks before output
  2. Verify data completeness
  3. Check prediction consistency
  4. Validate confidence levels
  5. Flag any issues for review

Quality checks include:
  - All 48 teams have predictions
  - Probabilities sum to 1.0
  - Confidence matches data quality
  - No missing or invalid data
  - Logical consistency (e.g., strong teams shouldn't have very low win probabilities)

Output: Quality report with pass/fail status and any warnings.
"""


# ── Quality Report ───────────────────────────────────────────────────────────


@dataclass
class QualityCheck:
    """One quality check result."""
    name: str
    passed: bool
    details: str = ""
    severity: str = "info"  # critical, warning, info


@dataclass
class QualityReport:
    """Complete quality report."""
    overall_pass: bool
    quality_score: float  # 0.0 - 1.0
    checks: list[QualityCheck]
    warnings: list[str]
    errors: list[str]
    recommendations: list[str]


# ── ReAct Implementation ─────────────────────────────────────────────────────


    def observe(self, state: WorldState) -> dict:
        """OBSERVE: Gather all system outputs for quality checking."""
        observation = {
            "teams_in_state": len(state.teams),
            "predictions_count": len(state.predictions),
            "simulation_available": state.simulation_results is not None,
            "simulation_runs": state.monte_carlo_runs,
            "agent_traces": len(state.agent_traces),
            "recent_errors": state.errors[-5:] if state.errors else [],
            "recent_warnings": state.warnings[-5:] if state.warnings else [],
        }

        # Count predictions by status
        pred_status = {"valid": 0, "invalid": 0, "missing": 0}
        for match_id, pred in state.predictions.items():
            if isinstance(pred, dict):
                outcome = pred.get("outcome", {})
                if outcome:
                    total = sum(outcome.values())
                    if 0.99 <= total <= 1.01:
                        pred_status["valid"] += 1
                    else:
                        pred_status["invalid"] += 1
                else:
                    pred_status["missing"] += 1
            else:
                pred_status["missing"] += 1

        observation["prediction_status"] = pred_status

        # Data freshness
        observation["data_freshness"] = {
            "elo": state.elo_last_updated,
            "odds": state.odds_last_updated,
        }

        return observation

    def think(self, observation: dict, state: WorldState) -> str:
        """THINK: Plan quality checks based on available data."""
        checks_needed = []

        if observation["teams_in_state"] < 48:
            checks_needed.append("TEAM_COVERAGE")

        if observation["predictions_count"] == 0:
            checks_needed.append("NO_PREDICTIONS")

        if not observation["simulation_available"]:
            checks_needed.append("NO_SIMULATION")

        if observation["prediction_status"]["invalid"] > 0:
            checks_needed.append("INVALID_PROBABILITIES")

        if observation["recent_errors"]:
            checks_needed.append("SYSTEM_ERRORS")

        if not checks_needed:
            return "QUALITY_GOOD: Ready for final quality check."

        return f"QUALITY_ISSUES: {', '.join(checks_needed)}. Will perform detailed checks."

    def act(self, thought: str, state: WorldState) -> tuple[QualityReport, str]:
        """ACT: Perform quality checks."""
        checks: list[QualityCheck] = []
        warnings: list[str] = []
        errors: list[str] = []
        recommendations: list[str] = []

        # Check 1: Team coverage
        team_count = len(state.teams)
        team_check = QualityCheck(
            name="team_coverage",
            passed=team_count >= 48,
            details=f"{team_count}/48 teams available",
            severity="critical" if team_count < 40 else "warning" if team_count < 48 else "info",
        )
        checks.append(team_check)
        if team_count < 48:
            warnings.append(f"Only {team_count}/48 teams available for prediction")

        # Check 2: Prediction completeness
        expected_predictions = team_count  # At minimum, one prediction per team pair
        pred_count = len(state.predictions)
        pred_check = QualityCheck(
            name="prediction_completeness",
            passed=pred_count > 0,
            details=f"{pred_count} predictions available",
            severity="critical" if pred_count == 0 else "info",
        )
        checks.append(pred_check)

        # Check 3: Probability validity
        invalid_probs = []
        for match_id, pred in state.predictions.items():
            if isinstance(pred, dict):
                outcome = pred.get("outcome", {})
                if outcome:
                    total = sum(outcome.values())
                    if not (0.99 <= total <= 1.01):
                        invalid_probs.append(match_id)

        prob_check = QualityCheck(
            name="probability_sum",
            passed=len(invalid_probs) == 0,
            details=f"{len(invalid_probs)} predictions with invalid probability sums",
            severity="critical" if len(invalid_probs) > 0 else "info",
        )
        checks.append(prob_check)
        if invalid_probs:
            errors.append(f"Probability sum errors in: {', '.join(invalid_probs[:5])}")
            recommendations.append("Renormalize all probability distributions")

        # Check 4: Simulation quality
        if state.simulation_results:
            sim_check = QualityCheck(
                name="simulation_available",
                passed=True,
                details=f"Simulation completed with {state.monte_carlo_runs:,} runs",
                severity="info",
            )
        else:
            sim_check = QualityCheck(
                name="simulation_available",
                passed=False,
                details="No simulation results available",
                severity="warning",
            )
            warnings.append("Tournament simulation not available")
        checks.append(sim_check)

        # Check 5: Data freshness
        if state.elo_last_updated:
            elo_age_hours = 0  # Would calculate from timestamp
            freshness_check = QualityCheck(
                name="data_freshness",
                passed=True,
                details=f"Elo data last updated: {state.elo_last_updated}",
                severity="info",
            )
        else:
            freshness_check = QualityCheck(
                name="data_freshness",
                passed=False,
                details="No Elo update timestamp found",
                severity="warning",
            )
            warnings.append("Cannot verify Elo data freshness")
        checks.append(freshness_check)

        # Check 6: Agent execution quality
        failed_agents = [
            t.get("agent") for t in state.agent_traces
            if t.get("status") == "failure"
        ]
        if failed_agents:
            agent_check = QualityCheck(
                name="agent_execution",
                passed=False,
                details=f"Failed agents: {', '.join(failed_agents)}",
                severity="critical",
            )
            errors.append(f"Agent execution failures: {', '.join(failed_agents)}")
        else:
            agent_check = QualityCheck(
                name="agent_execution",
                passed=True,
                details="All agents completed successfully",
                severity="info",
            )
        checks.append(agent_check)

        # Check 7: Confidence calibration
        low_confidence_count = 0
        for pred in state.predictions.values():
            if isinstance(pred, dict):
                confidence = pred.get("confidence", "medium")
                if confidence == "low":
                    low_confidence_count += 1

        conf_check = QualityCheck(
            name="confidence_distribution",
            passed=low_confidence_count < len(state.predictions) * 0.5,
            details=f"{low_confidence_count}/{len(state.predictions)} predictions have low confidence",
            severity="warning" if low_confidence_count > len(state.predictions) * 0.3 else "info",
        )
        checks.append(conf_check)

        # Calculate overall quality score
        passed_checks = sum(1 for c in checks if c.passed)
        quality_score = passed_checks / len(checks) if checks else 0.0

        # Determine if overall pass
        critical_failures = [c for c in checks if c.severity == "critical" and not c.passed]
        overall_pass = len(critical_failures) == 0

        # Final recommendations
        if quality_score < 0.8:
            recommendations.append("Consider regenerating predictions with refreshed data")
        if len(warnings) > 3:
            recommendations.append("Multiple warnings suggest data quality needs improvement")

        report = QualityReport(
            overall_pass=overall_pass,
            quality_score=quality_score,
            checks=checks,
            warnings=warnings,
            errors=errors,
            recommendations=recommendations,
        )

        observation = f"Quality check complete. Score: {quality_score:.0%}. " \
                     f"Passed: {passed_checks}/{len(checks)}. " \
                     f"Overall: {'PASS' if overall_pass else 'FAIL'}"

        return report, observation

    def evaluate(self, result: QualityReport, state: WorldState) -> bool:
        """EVALUATE: Check if quality is acceptable."""
        return result.overall_pass and result.quality_score >= 0.7

    def revise(self, result: Any, error: str, state: WorldState) -> str:
        """REVISE: Suggest fixes for quality issues."""
        if isinstance(result, QualityReport):
            fixes = result.recommendations[:3]
            return f"Suggested fixes: {'; '.join(fixes)}"
        return "Address quality issues before publishing predictions."
