"""WC2026 Multi-Agent System — Main Entry Point.

This module provides the main system class that ties all agents together.

Usage:
  from worldcup_agent.multi_agent import WC2026MultiAgent

  # Initialize
  system = WC2026MultiAgent()

  # Run full prediction pipeline
  result = system.run_full_pipeline()

  # Or run specific task
  result = system.run_task(TaskType.PREDICT_MATCH, match_id="arg_vs_mex")
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from worldcup_agent.multi_agent.core import (
    WorldState,
    TaskType,
    WC2026AgentSystem,
)
from worldcup_agent.multi_agent.agents import (
    DataAgent,
    AnalysisAgent,
    SimulationAgent,
    ReflectionAgent,
    ExplainerAgent,
    QualityAgent,
)


# ── Result Types ──────────────────────────────────────────────────────────────


@dataclass
class PipelineResult:
    """Result of a full pipeline run."""
    success: bool
    state: WorldState
    quality_score: float
    trace: list[dict]
    output_path: Path | None = None
    error: str | None = None


from dataclasses import dataclass


# ── Main System ──────────────────────────────────────────────────────────────


class WC2026MultiAgent:
    """
    Main multi-agent system for WC2026 predictions.

    This class orchestrates all agents to produce tournament predictions.

    Key features:
      - Full ReAct implementation in each agent
      - Shared World State for inter-agent communication
      - Monte Carlo simulation for tournament prediction
      - Self-correction through Reflection Agent
      - Quality assurance through Quality Agent
    """

    def __init__(self, simulation_runs: int = 10_000):
        # Initialize base system
        self.system = WC2026AgentSystem()

        # Initialize and register all agents
        self._register_agents(simulation_runs)

        # Output directory
        self.output_dir = Path(__file__).resolve().parents[2] / "data" / "multi_agent"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _register_agents(self, simulation_runs: int) -> None:
        """Register all agents with the system."""
        self.data_agent = DataAgent()
        self.analysis_agent = AnalysisAgent()
        self.simulation_agent = SimulationAgent(default_runs=simulation_runs)
        self.reflection_agent = ReflectionAgent()
        self.explainer_agent = ExplainerAgent()
        self.quality_agent = QualityAgent()

        self.system.register_agent(self.data_agent)
        self.system.register_agent(self.analysis_agent)
        self.system.register_agent(self.simulation_agent)
        self.system.register_agent(self.reflection_agent)
        self.system.register_agent(self.explainer_agent)
        self.system.register_agent(self.quality_agent)

    def run_full_pipeline(self) -> PipelineResult:
        """
        Run the complete prediction pipeline.

        This executes all agents in sequence:
          1. Data Agent → Check and load data
          2. Analysis Agent → Analyze team strengths
          3. Simulation Agent → Run Monte Carlo simulation
          4. Reflection Agent → Self-check
          5. Explainer Agent → Generate narratives
          6. Quality Agent → Final quality check
        """
        print("=" * 60)
        print("WC2026 Multi-Agent System — Full Pipeline")
        print("=" * 60)

        # Run through orchestrator
        self.system.state = self.system.run(TaskType.PREDICT_TOURNAMENT)

        # Calculate quality score
        quality_score = self._calculate_quality_score()

        # Determine success
        has_errors = len(self.system.state.errors) > 0
        success = quality_score >= 0.7 and not has_errors

        # Save output
        output_path = None
        if success:
            output_path = self._save_output()

        print("\n" + "=" * 60)
        print("Pipeline Complete")
        print("=" * 60)
        print(f"Success: {success}")
        print(f"Quality Score: {quality_score:.0%}")
        print(f"Agents Run: {len(self.system.state.agent_traces)}")
        print(f"Teams Loaded: {len(self.system.state.teams)}")
        print(f"Simulation Runs: {self.system.state.monte_carlo_runs:,}")

        if output_path:
            print(f"Output: {output_path}")

        return PipelineResult(
            success=success,
            state=self.system.state,
            quality_score=quality_score,
            trace=self.system.state.agent_traces,
            output_path=output_path,
            error=self.system.state.errors[-1] if self.system.state.errors else None,
        )

    def run_task(self, task_type: TaskType, **kwargs) -> WorldState:
        """Run a specific task type."""
        print(f"\nRunning task: {task_type.value}")

        self.system.state = self.system.run(task_type)

        return self.system.state

    def run_with_loop(self, interval_seconds: int = 3600) -> None:
        """
        Run the system in a continuous loop (for production use).

        This is the closed-loop mode that:
          1. Periodically checks for new data
          2. Updates World State
          3. Re-runs predictions
          4. Validates quality
        """
        import time

        print(f"Starting closed-loop mode (interval: {interval_seconds}s)")
        print("Press Ctrl+C to stop")

        iteration = 0
        while True:
            iteration += 1
            print(f"\n{'=' * 60}")
            print(f"Loop Iteration #{iteration} — {datetime.now():%Y-%m-%d %H:%M:%S}")
            print(f"{'=' * 60}")

            try:
                result = self.run_full_pipeline()

                if result.success:
                    print("Pipeline succeeded")
                else:
                    print(f"Pipeline failed: {result.error}")

            except KeyboardInterrupt:
                print("\nStopping loop...")
                break

            except Exception as e:
                print(f"Error in loop: {e}")

            print(f"\nSleeping for {interval_seconds}s...")
            time.sleep(interval_seconds)

    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score from agent traces."""
        if not self.system.state.agent_traces:
            return 0.0

        successful_agents = sum(
            1 for t in self.system.state.agent_traces
            if t.get("status") == "success"
        )

        total_agents = len(self.system.state.agent_traces)

        # Base score from successful agents
        score = successful_agents / total_agents if total_agents > 0 else 0.0

        # Adjust for warnings and errors
        score -= len(self.system.state.warnings) * 0.05
        score -= len(self.system.state.errors) * 0.1

        return max(0.0, min(1.0, score))

    def _save_output(self) -> Path:
        """Save the output to JSON file."""
        output = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tournament": "FIFA World Cup 2026",
            "quality_score": self._calculate_quality_score(),
            "state": self.system.state.to_dict(),
            "agent_traces": self.system.state.agent_traces,
        }

        # Generate filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"multi_agent_output_{timestamp}.json"
        output_path = self.output_dir / filename

        output_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return output_path

    def get_status(self) -> dict:
        """Get current system status."""
        return {
            "agents_registered": len(self.system.agents),
            "teams_loaded": len(self.system.state.teams),
            "simulation_available": self.system.state.simulation_results is not None,
            "monte_carlo_runs": self.system.state.monte_carlo_runs,
            "last_task": self.system.state.current_task,
            "recent_errors": self.system.state.errors[-3:] if self.system.state.errors else [],
            "recent_warnings": self.system.state.warnings[-3:] if self.system.state.warnings else [],
        }

    def get_trace(self) -> list[dict]:
        """Get execution trace for debugging."""
        return self.system.state.agent_traces


# ── CLI Entry Point ──────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="WC2026 Multi-Agent Prediction System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline once
  python -m worldcup_agent.multi_agent.main

  # Run in loop mode (check every hour)
  python -m worldcup_agent.multi_agent.main --loop

  # Run with custom simulation runs
  python -m worldcup_agent.multi_agent.main --runs 50000

  # Check system status
  python -m worldcup_agent.multi_agent.main --status
"""
    )

    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run in continuous loop mode",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="Loop interval in seconds (default: 3600)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=10_000,
        help="Number of Monte Carlo simulation runs (default: 10000)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check system status and exit",
    )

    args = parser.parse_args()

    # Initialize system
    system = WC2026MultiAgent(simulation_runs=args.runs)

    if args.status:
        # Just check status
        status = system.get_status()
        print(json.dumps(status, indent=2))
        return

    if args.loop:
        # Run in loop mode
        system.run_with_loop(interval_seconds=args.interval)
    else:
        # Run once
        result = system.run_full_pipeline()

        if result.success:
            print(f"\nOutput saved to: {result.output_path}")
        else:
            print(f"\nPipeline failed: {result.error}")
            exit(1)


if __name__ == "__main__":
    main()
