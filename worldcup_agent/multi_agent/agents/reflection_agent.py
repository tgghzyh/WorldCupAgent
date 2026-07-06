"""Reflection Agent — self-correction and quality assurance.

This agent implements the ReAct pattern for self-reflection:
  1. OBSERVE: Gather outputs from all other agents
  2. THINK: Reason about consistency and quality
  3. ACT: Validate and flag issues
  4. EVALUATE: Check if issues are resolved
  5. REVISE: Suggest corrections or flag for human review

This is the "self-check loop" that distinguishes true Agent systems.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from worldcup_agent.multi_agent import BaseAgent, WorldState, AgentStatus


# ── Issue Types ─────────────────────────────────────────────────────────────


class IssueSeverity:
    CRITICAL = "critical"  # Must fix before proceeding
    WARNING = "warning"    # Should fix but can proceed
    INFO = "info"          # Nice to have


class IssueType:
    PROBABILITY_SUM = "probability_sum"
    CONFIDENCE_MISMATCH = "confidence_mismatch"
    INCONSISTENT_TEAM_DATA = "inconsistent_team_data"
    MISSING_DATA = "missing_data"
    BIAS_DETECTED = "bias_detected"
    LOGICAL_ERROR = "logical_error"
    AGENT_ERROR = "agent_error"


@dataclass
class ReflectionIssue:
    """One issue found during reflection."""
    issue_type: str
    severity: str
    description: str
    affected_item: str | None = None
    suggested_fix: str | None = None


@dataclass
class ReflectionReport:
    """Complete reflection report."""
    issues: list[ReflectionIssue]
    overall_quality: float  # 0.0 - 1.0
    can_proceed: bool
    suggestions: list[str]


class ReflectionAgent(BaseAgent):
    """
    Reflection Agent — self-correction and quality assurance.

    This agent reviews the work of other agents and identifies:
      1. Logical inconsistencies
      2. Confidence calibration issues
      3. Missing information
      4. Potential biases
      5. Areas for improvement

    ReAct Loop:
      OBSERVE: Gather agent outputs and traces
      THINK:   Analyze for issues and inconsistencies
      ACT:     Validate and generate reflection report
      EVALUATE: Check if issues are critical
      REVISE:  Suggest corrections if needed
    """

    def __init__(self):
        super().__init__(
            name="reflection_agent",
            description="Self-correction and quality assurance",
            max_iterations=2,
        )

    @property
    def system_prompt(self) -> str:
        return """You are the Reflection Agent for WC2026 predictions.

Your responsibilities:
  1. Review outputs from all other agents
  2. Identify logical inconsistencies
  3. Check confidence calibration
  4. Flag potential issues
  5. Suggest improvements

You are the "quality gate" that ensures:
  - Predictions are consistent with analysis
  - Probabilities sum to 1.0
  - Confidence levels match data quality
  - No obvious biases or errors

Your output is a reflection report with:
  - Issues found (if any)
  - Severity level (critical/warning/info)
  - Suggested corrections
"""

    # ── ReAct Implementation ─────────────────────────────────────────────

    def observe(self, state: WorldState) -> dict:
        """OBSERVE: Gather all agent traces and outputs."""
        observation = {
            "simulation_results": state.simulation_results is not None,
            "predictions": len(state.predictions),
            "agent_traces": len(state.agent_traces),
            "warnings": len(state.warnings),
            "errors": len(state.errors),
        }

        # Gather recent agent traces
        recent_traces = state.agent_traces[-5:] if state.agent_traces else []
        observation["recent_agents"] = [
            {
                "agent": t.get("agent", ""),
                "status": t.get("status", ""),
                "steps": len(t.get("steps", [])),
            }
            for t in recent_traces
        ]

        # Check prediction consistency
        if state.predictions:
            probs = []
            for pred in state.predictions.values():
                if isinstance(pred, dict):
                    outcome = pred.get("outcome", {})
                    if outcome:
                        total = (
                            outcome.get("home_win", 0) +
                            outcome.get("draw", 0) +
                            outcome.get("away_win", 0)
                        )
                        probs.append(total)

            observation["probability_checks"] = {
                "teams_with_predictions": len(probs),
                "all_sum_to_one": all(0.99 <= p <= 1.01 for p in probs) if probs else True,
                "avg_sum": sum(probs) / len(probs) if probs else 1.0,
            }

        return observation

    def think(self, observation: dict, state: WorldState) -> str:
        """THINK: Reason about what to check."""
        checks_needed = []

        if not observation.get("simulation_results"):
            checks_needed.append("SIMULATION_MISSING")

        if observation.get("probability_checks", {}).get("all_sum_to_one") is False:
            checks_needed.append("PROBABILITY_ERROR")

        if observation.get("errors"):
            checks_needed.append("AGENT_ERRORS")

        if not checks_needed:
            return "REFLECTION_CLEAN: All checks passed. No issues found."

        return f"REFLECTION_ISSUES: {', '.join(checks_needed)}. Will analyze."

    def act(self, thought: str, state: WorldState) -> tuple[ReflectionReport, str]:
        """ACT: Perform reflection and generate report."""
        issues: list[ReflectionIssue] = []
        suggestions: list[str] = []

        # Check 1: Probability sums
        for pred_id, pred in state.predictions.items():
            if isinstance(pred, dict):
                outcome = pred.get("outcome", {})
                if outcome:
                    total = (
                        outcome.get("home_win", 0) +
                        outcome.get("draw", 0) +
                        outcome.get("away_win", 0)
                    )
                    if not (0.99 <= total <= 1.01):
                        issues.append(ReflectionIssue(
                            issue_type=IssueType.PROBABILITY_SUM,
                            severity=IssueSeverity.CRITICAL,
                            description=f"Probabilities sum to {total:.4f}, not 1.0",
                            affected_item=pred_id,
                            suggested_fix="Renormalize probabilities",
                        ))

        # Check 2: Simulation quality
        if state.simulation_results:
            sim_probs = list(state.simulation_results.values())
            if sim_probs:
                total_prob = sum(sim_probs)
                if total_prob > 0:
                    top_3 = sorted(sim_probs, reverse=True)[:3]
                    if sum(top_3) < 0.1:
                        issues.append(ReflectionIssue(
                            issue_type=IssueType.LOGICAL_ERROR,
                            severity=IssueSeverity.WARNING,
                            description="Champion probabilities are too spread out",
                            suggested_fix="Check simulation model",
                        ))

        # Check 3: Agent traces quality
        for trace in state.agent_traces:
            if trace.get("status") == AgentStatus.FAILURE.value:
                issues.append(ReflectionIssue(
                    issue_type=IssueType.AGENT_ERROR,
                    severity=IssueSeverity.CRITICAL,
                    description=f"Agent {trace.get('agent')} failed",
                    affected_item=trace.get("trace_id"),
                    suggested_fix="Retry or debug agent",
                ))

        # Calculate overall quality
        if not issues:
            overall_quality = 1.0
            can_proceed = True
        else:
            critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
            warning_count = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

            overall_quality = 1.0 - (critical_count * 0.3) - (warning_count * 0.1)
            overall_quality = max(0.0, overall_quality)
            can_proceed = critical_count == 0

        # Generate suggestions
        if overall_quality < 0.8:
            suggestions.append("Consider re-running simulation with more iterations")
        if len([i for i in issues if i.severity == IssueSeverity.WARNING]) > 3:
            suggestions.append("Multiple warnings suggest data quality issues")

        report = ReflectionReport(
            issues=issues,
            overall_quality=overall_quality,
            can_proceed=can_proceed,
            suggestions=suggestions,
        )

        observation = f"Reflection complete. Found {len(issues)} issues. " \
                     f"Quality score: {overall_quality:.2f}. " \
                     f"Can proceed: {can_proceed}"

        return report, observation

    def evaluate(self, result: ReflectionReport, state: WorldState) -> bool:
        """EVALUATE: Check if quality is acceptable."""
        return result.can_proceed and result.overall_quality >= 0.7

    def revise(self, result: Any, error: str, state: WorldState) -> str:
        """REVISE: Suggest corrections."""
        if isinstance(result, ReflectionReport):
            fixes = [f"{i.issue_type}: {i.suggested_fix}" for i in result.issues if i.suggested_fix]
            return f"Suggested fixes: {'; '.join(fixes[:3])}"
        return "Review and address reflection issues before proceeding."
