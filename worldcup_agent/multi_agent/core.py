"""Core types for the WC2026 Multi-Agent System.

This module contains the foundational types used throughout the system:
  - WorldState: Shared state for inter-agent communication
  - TaskType: Types of tasks the system handles
  - AgentStatus: Status codes for agent execution
  - ReActStep / AgentTrace: Execution tracking
  - BaseAgent: Base class for all agents
  - Orchestrator: Task planning and coordination
  - WC2026AgentSystem: Main system class
"""
from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskType(Enum):
    """Types of tasks the system can handle."""
    PREDICT_MATCH = "predict_match"
    PREDICT_TOURNAMENT = "predict_tournament"
    ANALYZE_RESULTS = "analyze_results"
    UPDATE_STATE = "update_state"
    EXPLAIN_PREDICTION = "explain_prediction"
    SIMULATE_BRACKET = "simulate_bracket"


class AgentStatus(Enum):
    """Status of an agent after execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEEDS_RETRY = "needs_retry"
    NEEDS_HUMAN_INPUT = "needs_human_input"
    INCOMPLETE = "incomplete"


class StepStatus(Enum):
    """Status of a ReAct step."""
    OBSERVE = "observe"
    THINK = "think"
    ACT = "act"
    EVALUATE = "evaluate"
    REVISE = "revise"
    COMPLETE = "complete"


@dataclass
class WorldState:
    """
    Shared World State — the single source of truth for all agents.

    Unlike a pipeline where data is passed directly between stages,
    agents read from and write to this shared state.

    This enables:
    - True parallelism (agents don't block each other)
    - Shared context (any agent can see what others did)
    - Easier debugging (state is observable)
    """
    tournament_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tournament_stage: str = "group"
    teams: dict[str, dict] = field(default_factory=dict)
    match_results: list[dict] = field(default_factory=list)
    predictions: dict[str, dict] = field(default_factory=dict)
    simulation_results: dict | None = None
    monte_carlo_runs: int = 0
    elo_last_updated: str | None = None
    odds_last_updated: str | None = None
    injury_last_updated: str | None = None
    agent_traces: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    current_task: str | None = None
    task_history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tournament_date": self.tournament_date,
            "tournament_stage": self.tournament_stage,
            "teams": self.teams,
            "match_results": self.match_results,
            "predictions": self.predictions,
            "simulation_results": self.simulation_results,
            "monte_carlo_runs": self.monte_carlo_runs,
            "data_freshness": {
                "elo": self.elo_last_updated,
                "odds": self.odds_last_updated,
                "injury": self.injury_last_updated,
            },
            "agent_traces": self.agent_traces,
            "errors": self.errors,
            "warnings": self.warnings,
            "current_task": self.current_task,
        }

    @classmethod
    def from_dict(cls, d: dict) -> WorldState:
        state = cls()
        state.tournament_date = d.get("tournament_date", state.tournament_date)
        state.tournament_stage = d.get("tournament_stage", "group")
        state.teams = d.get("teams", {})
        state.match_results = d.get("match_results", [])
        state.predictions = d.get("predictions", {})
        state.simulation_results = d.get("simulation_results")
        state.monte_carlo_runs = d.get("monte_carlo_runs", 0)
        state.elo_last_updated = d.get("data_freshness", {}).get("elo")
        state.odds_last_updated = d.get("data_freshness", {}).get("odds")
        state.injury_last_updated = d.get("data_freshness", {}).get("injury")
        state.agent_traces = d.get("agent_traces", [])
        state.errors = d.get("errors", [])
        state.warnings = d.get("warnings", [])
        state.current_task = d.get("current_task")
        return state


@dataclass
class ReActStep:
    """One step in the ReAct reasoning loop."""
    step_type: StepStatus
    thought: str = ""
    action: str = ""
    observation: str = ""
    result: Any = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "step": self.step_type.value,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentTrace:
    """Complete trace of an agent's execution."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_name: str = ""
    task: str = ""
    status: AgentStatus = AgentStatus.INCOMPLETE
    steps: list[ReActStep] = field(default_factory=list)
    final_result: Any = None
    error: str | None = None
    duration_ms: float = 0.0

    def add_step(self, step: ReActStep) -> None:
        self.steps.append(step)

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "agent": self.agent_name,
            "task": self.task,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "final_result": str(self.final_result) if self.final_result else None,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
        }


@dataclass
class AgentMessage:
    """Message passed between agents via World State."""
    from_agent: str
    to_agent: str | None
    action: str
    payload: dict
    trace_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "from": self.from_agent,
            "to": self.to_agent,
            "action": self.action,
            "payload": self.payload,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
        }


class BaseAgent(ABC):
    """
    Base class for all agents in the system.

    Each agent implements the ReAct pattern:
      1. OBSERVE — gather information from World State
      2. THINK — reason about what to do
      3. ACT — execute the chosen action
      4. EVALUATE — check if the result is satisfactory
      5. REVISE — if not, revise and try again
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        max_iterations: int = 3,
    ):
        self.name = name
        self.description = description
        self.max_iterations = max_iterations

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The agent's role and responsibilities."""
        pass

    @abstractmethod
    def observe(self, state: WorldState) -> dict:
        """OBSERVE step: Gather information from World State."""
        pass

    @abstractmethod
    def think(self, observation: dict, state: WorldState) -> str:
        """THINK step: Reason about what to do based on observation."""
        pass

    @abstractmethod
    def act(self, thought: str, state: WorldState) -> tuple[Any, str]:
        """
        ACT step: Execute the chosen action.

        Returns:
          - result: The result of the action
          - observation: What was observed after the action
        """
        pass

    @abstractmethod
    def evaluate(self, result: Any, state: WorldState) -> bool:
        """EVALUATE step: Check if the result is satisfactory."""
        pass

    def revise(self, result: Any, error: str, state: WorldState) -> str:
        """REVISE step: Revise approach based on error."""
        return f"Attempting to revise approach due to: {error}"

    def run(self, task: str, state: WorldState) -> AgentTrace:
        """
        Execute the ReAct loop for this agent.

        The loop continues until:
          - MAX_ITERATIONS reached
          - Evaluation passes
          - Unrecoverable error
        """
        trace = AgentTrace(agent_name=self.name, task=task)
        start_time = time.time()

        for iteration in range(self.max_iterations):
            try:
                observation = self.observe(state)
                trace.add_step(ReActStep(
                    step_type=StepStatus.OBSERVE,
                    observation=f"Observed {len(observation)} items",
                    result=observation,
                ))

                thought = self.think(observation, state)
                trace.add_step(ReActStep(
                    step_type=StepStatus.THINK,
                    thought=thought,
                ))

                result, action_obs = self.act(thought, state)
                trace.add_step(ReActStep(
                    step_type=StepStatus.ACT,
                    action=thought,
                    observation=action_obs,
                    result=result,
                ))

                success = self.evaluate(result, state)
                trace.add_step(ReActStep(
                    step_type=StepStatus.EVALUATE,
                    thought=f"Evaluation: {'SUCCESS' if success else 'NEEDS_REVISION'}",
                    observation=f"Result quality: {success}",
                ))

                if success:
                    trace.status = AgentStatus.SUCCESS
                    trace.final_result = result
                    break

                if iteration < self.max_iterations - 1:
                    revision = self.revise(result, "Quality check failed", state)
                    trace.add_step(ReActStep(
                        step_type=StepStatus.REVISE,
                        thought=revision,
                    ))

            except Exception as e:
                trace.add_step(ReActStep(
                    step_type=StepStatus.ACT,
                    error=str(e),
                ))
                trace.status = AgentStatus.FAILURE
                trace.error = str(e)
                break

        if trace.status == AgentStatus.INCOMPLETE:
            trace.status = AgentStatus.NEEDS_RETRY
            trace.error = "Max iterations reached"

        trace.duration_ms = (time.time() - start_time) * 1000
        return trace


class Orchestrator:
    """
    Orchestrator — the system's planner and scheduler.

    Key distinction from pipelines:
      - Does NOT control execution flow
      - Decides WHAT to do (task selection)
      - Agents decide HOW to do it
      - Monitors for failures and triggers re-planning
    """

    def __init__(self, agents: dict[str, BaseAgent]):
        self.agents = agents
        self.state = WorldState()
        self.execution_history: list[dict] = []

    def plan(self, task: TaskType) -> list[tuple[str, str]]:
        """Plan which agents to run and in what order."""
        self.state.current_task = task.value

        if task == TaskType.PREDICT_TOURNAMENT:
            return [
                ("data_agent", "check_and_refresh_data"),
                ("analysis_agent", "analyze_team_strengths"),
                ("simulation_agent", "run_monte_carlo"),
                ("reflection_agent", "validate_simulation"),
                ("explainer_agent", "generate_narratives"),
                ("quality_agent", "final_quality_check"),
            ]
        elif task == TaskType.PREDICT_MATCH:
            return [
                ("data_agent", "check_data_freshness"),
                ("analysis_agent", "analyze_matchup"),
                ("simulation_agent", "simulate_single_match"),
                ("explainer_agent", "explain_prediction"),
            ]
        elif task == TaskType.UPDATE_STATE:
            return [
                ("data_agent", "check_new_results"),
                ("analysis_agent", "analyze_new_results"),
                ("reflection_agent", "update_team_strengths"),
            ]
        elif task == TaskType.ANALYZE_RESULTS:
            return [
                ("analysis_agent", "analyze_tournament_progress"),
                ("simulation_agent", "update_bracket_simulation"),
                ("quality_agent", "evaluate_prediction_accuracy"),
            ]
        return []

    def should_replan(self, trace: AgentTrace) -> bool:
        """Decide if we need to replan based on agent execution."""
        if trace.status in (AgentStatus.FAILURE, AgentStatus.NEEDS_RETRY):
            return True
        if len(self.state.warnings) > 3:
            return True
        return False

    def run(self, task: TaskType) -> WorldState:
        """Execute the planned tasks."""
        plan = self.plan(task)

        for agent_name, task_desc in plan:
            if agent_name not in self.agents:
                self.state.errors.append(f"Agent {agent_name} not found")
                continue

            agent = self.agents[agent_name]
            trace = agent.run(task_desc, self.state)

            self.state.agent_traces.append(trace.to_dict())
            self.execution_history.append({
                "agent": agent_name,
                "task": task_desc,
                "status": trace.status.value,
                "duration_ms": trace.duration_ms,
            })

            if self.should_replan(trace):
                self.state.warnings.append(
                    f"Agent {agent_name} reported issues, continuing..."
                )

        self.state.task_history.append({
            "task": task.value,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "agents_run": len(plan),
        })

        return self.state


class WC2026AgentSystem:
    """The main multi-agent system for WC2026 predictions."""

    def __init__(self):
        self.state = WorldState()
        self.agents: dict[str, BaseAgent] = {}
        self.orchestrator = Orchestrator(self.agents)

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the system."""
        self.agents[agent.name] = agent
        self.orchestrator.agents[agent.name] = agent

    def run(self, task: TaskType) -> WorldState:
        """Run the system for a given task."""
        self.state = self.orchestrator.run(task)
        return self.state

    def get_trace(self) -> list[dict]:
        """Get the execution trace for debugging/visualization."""
        return self.state.agent_traces
