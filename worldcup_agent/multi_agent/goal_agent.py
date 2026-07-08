"""Goal-Driven Agent Framework.

This module upgrades the BaseAgent from a "task executor" to a "goal-driven agent"
that can:

1. DECLARE GOALS: Agents specify what they want to achieve
2. SELF-ASSESS: Agents evaluate whether goals are met
3. AUTONOMOUS DECISION: Agents decide next steps without Orchestrator control
4. GOAL REFINEMENT: Agents can refine goals based on results

Key principle:
  "Orchestrator suggests, Agent decides"
  vs the old: "Orchestrator commands, Agent executes"
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from worldcup_agent.multi_agent.core import (
    WorldState,
    AgentStatus,
    ReActStep,
    StepStatus,
    AgentTrace,
)
from worldcup_agent.multi_agent.cognitive_model import (
    CognitiveWorldModel,
    Belief,
    Evidence,
    EvidenceSource,
    EvidenceQuality,
)


# ── Goal Types ────────────────────────────────────────────────────────────────


class GoalType(Enum):
    """Types of goals an agent can have."""
    ACQUIRE_DATA = "acquire_data"              # Get specific data
    ANALYZE = "analyze"                        # Analyze something
    PREDICT = "predict"                        # Make a prediction
    VERIFY = "verify"                          # Verify something
    EXPLAIN = "explain"                        # Generate explanation
    SIMULATE = "simulate"                      # Run simulation
    RESOLVE_CONFLICT = "resolve_conflict"     # Resolve a conflict
    COLLECT_EVIDENCE = "collect_evidence"     # Collect evidence for a belief
    REFINE_PREDICTION = "refine_prediction"   # Improve an existing prediction


class GoalStatus(Enum):
    """Status of a goal."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    PARTIALLY_ACHIEVED = "partially_achieved"
    FAILED = "failed"
    ABANDONED = "abandoned"


class DecisionType(Enum):
    """Decisions an agent can make autonomously."""
    CONTINUE = "continue"              # Continue current approach
    RETRY = "retry"                  # Retry with different approach
    REQUEST_INFO = "request_info"    # Ask for more information
    REQUEST_HELP = "request_help"    # Ask other agent for help
    ESCALATE = "escalate"            # Escalate to human/Orchestrator
    REFINE_GOAL = "refine_goal"      # Refine the goal
    SPLIT_GOAL = "split_goal"        # Split into sub-goals


# ── Goal Definition ──────────────────────────────────────────────────────────


@dataclass
class Goal:
    """
    A goal that an agent is working towards.

    Unlike a task (which is externally assigned), a goal is self-declared
    and the agent is responsible for:
      - Deciding whether it's achieved
      - Deciding what to do if not
      - Refining the goal if needed
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal_type: GoalType
    description: str
    target: str | None = None        # What this goal is about

    # Parameters
    parameters: dict = field(default_factory=dict)
    constraints: dict = field(default_factory=dict)  # e.g., max_retries, timeout

    # Status
    status: GoalStatus = GoalStatus.PENDING
    progress: float = 0.0           # 0.0 - 1.0

    # Progress tracking
    attempts: int = 0
    max_attempts: int = 3
    strategies_tried: list[str] = field(default_factory=list)

    # Results
    result: Any = None
    confidence: float = 0.0

    # Self-assessment criteria
    success_criteria: list[str] = field(default_factory=list)
    partial_success_threshold: float = 0.7

    # Meta
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parent_goal_id: str | None = None  # For hierarchical goals

    def assess_progress(self, result: Any, state: WorldState) -> GoalStatus:
        """
        Self-assess whether goal is achieved.

        This is the key to goal-driven autonomy:
        the agent decides whether it succeeded.
        """
        self.attempts += 1
        self.result = result
        self.updated_at = datetime.now(timezone.utc).isoformat()

        # Check success criteria
        criteria_met = 0
        for criterion in self.success_criteria:
            if self._check_criterion(criterion, result, state):
                criteria_met += 1

        if criteria_met == len(self.success_criteria):
            self.status = GoalStatus.ACHIEVED
            self.progress = 1.0
            return GoalStatus.ACHIEVED

        if criteria_met > 0 and criteria_met / max(1, len(self.success_criteria)) >= self.partial_success_threshold:
            self.status = GoalStatus.PARTIALLY_ACHIEVED
            self.progress = criteria_met / len(self.success_criteria)
            return GoalStatus.PARTIALLY_ACHIEVED

        # Check if max attempts reached
        if self.attempts >= self.max_attempts:
            self.status = GoalStatus.FAILED
            self.progress = criteria_met / max(1, len(self.success_criteria))
            return GoalStatus.FAILED

        # Still in progress
        self.status = GoalStatus.IN_PROGRESS
        self.progress = criteria_met / max(1, len(self.success_criteria)) * 0.5
        return GoalStatus.IN_PROGRESS

    def _check_criterion(self, criterion: str, result: Any, state: WorldState) -> bool:
        """Check if a success criterion is met."""
        # Simple string-based criteria
        if criterion.startswith("has_"):
            # e.g., "has_data"
            return result is not None and result != {}
        elif criterion.startswith("confidence_"):
            # e.g., "confidence_above_0.7"
            threshold = float(criterion.split("_")[1])
            return isinstance(result, dict) and result.get("confidence", 0) >= threshold
        elif criterion.startswith("count_"):
            # e.g., "count_above_10"
            threshold = int(criterion.split("_")[1])
            return isinstance(result, (list, dict)) and len(result) >= threshold
        return result is not None


@dataclass
class AgentDecision:
    """
    A decision made by an agent autonomously.

    This records the agent's reasoning for why it chose a particular action.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    decision_type: DecisionType
    reasoning: str

    # Context
    goal_id: str | None = None
    agent_id: str
    current_strategy: str
    alternatives_considered: list[str] = field(default_factory=list)

    # Confidence in decision
    confidence: float = 0.5
    risk_assessment: str = ""

    # What to do next
    next_action: str = ""
    next_agent: str | None = None

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.decision_type.value,
            "reasoning": self.reasoning,
            "goal_id": self.goal_id,
            "agent_id": self.agent_id,
            "current_strategy": self.current_strategy,
            "alternatives": self.alternatives_considered,
            "confidence": self.confidence,
            "next_action": self.next_action,
            "next_agent": self.next_agent,
            "timestamp": self.timestamp,
        }


# ── Goal-Driven Agent ────────────────────────────────────────────────────────


class GoalDrivenAgent:
    """
    Base class for goal-driven agents.

    Key difference from BaseAgent:
      - Agents declare goals, not just execute tasks
      - Agents self-assess success
      - Agents autonomously decide next steps
      - Agents can request help from other agents
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

        # Goal tracking
        self.current_goal: Goal | None = None
        self.goal_history: list[Goal] = []
        self.decisions: list[AgentDecision] = []

        # Cognitive model integration
        self.cognitive_model: CognitiveWorldModel | None = None

    def set_cognitive_model(self, model: CognitiveWorldModel) -> None:
        """Connect to cognitive world model."""
        self.cognitive_model = model

    # ── Goal Declaration ──────────────────────────────────────────────────

    def declare_goal(
        self,
        goal_type: GoalType,
        description: str,
        target: str | None = None,
        parameters: dict | None = None,
        constraints: dict | None = None,
        success_criteria: list[str] | None = None,
    ) -> Goal:
        """Declare a new goal to work towards."""
        goal = Goal(
            goal_type=goal_type,
            description=description,
            target=target,
            parameters=parameters or {},
            constraints=constraints or {},
            success_criteria=success_criteria or ["has_data"],
            max_attempts=constraints.get("max_attempts", 3) if constraints else 3,
        )
        self.current_goal = goal
        return goal

    def close_goal(self, status: GoalStatus) -> None:
        """Close the current goal."""
        if self.current_goal:
            self.current_goal.status = status
            self.goal_history.append(self.current_goal)
            self.current_goal = None

    # ── Autonomous Decision Making ────────────────────────────────────────

    def decide(
        self,
        result: Any,
        state: WorldState,
        goal: Goal,
    ) -> AgentDecision:
        """
        Make an autonomous decision about what to do next.

        This is the core of goal-driven autonomy:
          - Evaluate current state
          - Consider alternatives
          - Choose the best action
          - Record reasoning
        """
        decision = AgentDecision(
            decision_type=DecisionType.CONTINUE,
            reasoning="Default: continue if progress is good",
            agent_id=self.name,
            current_strategy=goal.parameters.get("strategy", "default"),
        )

        # Assess progress
        progress = goal.assess_progress(result, state)

        # Decision logic based on progress
        if progress == GoalStatus.ACHIEVED:
            decision.decision_type = DecisionType.CONTINUE
            decision.reasoning = "Goal achieved. Wrapping up."
            decision.next_action = "close_goal"

        elif progress == GoalStatus.PARTIALLY_ACHIEVED:
            # Decide: retry, accept partial, or escalate
            if goal.attempts < goal.max_attempts:
                decision.decision_type = DecisionType.RETRY
                decision.reasoning = f"Partially achieved ({goal.progress:.0%}). Attempting improvement."
                decision.next_action = "retry_with_refinement"
                decision.alternatives_considered = ["accept_partial", "retry", "escalate"]
            else:
                decision.decision_type = DecisionType.CONTINUE
                decision.reasoning = "Partially achieved but max attempts reached. Accepting result."
                decision.next_action = "close_goal"

        elif progress == GoalStatus.FAILED:
            decision.decision_type = DecisionType.ESCALATE
            decision.reasoning = "Goal failed after max attempts. Escalating."
            decision.next_action = "escalate"
            decision.next_agent = "orchestrator"
            decision.risk_assessment = "High: critical goal failed"

        else:  # IN_PROGRESS
            # Check if we need more info
            if self._needs_more_info(result, state):
                decision.decision_type = DecisionType.REQUEST_INFO
                decision.reasoning = "Need more information to proceed."
                decision.next_action = "request_info"
            elif goal.attempts >= goal.max_attempts // 2:
                decision.decision_type = DecisionType.REFINE_GOAL
                decision.reasoning = "Halfway through attempts. Refining approach."
                decision.next_action = "refine_goal"
            else:
                decision.decision_type = DecisionType.CONTINUE
                decision.reasoning = "Good progress. Continuing."
                decision.next_action = "continue"

        # Record decision
        self.decisions.append(decision)
        return decision

    def _needs_more_info(self, result: Any, state: WorldState) -> bool:
        """Check if agent needs more information to proceed."""
        # Simple heuristic: if result is empty or confidence is low
        if result is None:
            return True
        if isinstance(result, dict) and result.get("confidence", 1.0) < 0.5:
            return True
        if isinstance(result, (list, dict)) and len(result) == 0:
            return True
        return False

    # ── Belief Integration ───────────────────────────────────────────────

    def assert_belief(
        self,
        subject: str,
        predicate: str,
        value: Any,
        confidence: float = 0.5,
        evidence_source: EvidenceSource = EvidenceSource.AGENT_INFERENCE,
        evidence_quality: EvidenceQuality = EvidenceQuality.MEDIUM,
    ) -> Belief | None:
        """Assert a belief into the cognitive model."""
        if not self.cognitive_model:
            return None

        evidence = Evidence(
            source=evidence_source,
            content=f"From {self.name}: {predicate} = {value}",
            quality=evidence_quality,
            agent_id=self.name,
        )

        return self.cognitive_model.assert_belief(
            subject=subject,
            predicate=predicate,
            value=value,
            confidence=confidence,
            evidence=[evidence],
            agent_id=self.name,
        )

    # ── Collaboration ──────────────────────────────────────────────────

    def request_help(
        self,
        from_agent: str,
        help_type: str,
        context: dict,
    ) -> dict:
        """
        Request help from another agent.

        Returns a request record that can be sent to the other agent.
        """
        return {
            "type": "help_request",
            "from": self.name,
            "to": from_agent,
            "help_type": help_type,
            "context": context,
            "goal_id": self.current_goal.id if self.current_goal else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def receive_help(
        self,
        from_agent: str,
        help_type: str,
        response: Any,
    ) -> None:
        """Process a response to a help request."""
        # Update belief based on help received
        if self.cognitive_model and self.current_goal:
            self.assert_belief(
                subject=f"{from_agent}_help",
                predicate=help_type,
                value=response,
                confidence=0.8,
                evidence_source=EvidenceSource.AGENT_INFERENCE,
                evidence_quality=EvidenceQuality.HIGH,
            )


# ── Goal-Driven Orchestrator ────────────────────────────────────────────────


class GoalDrivenOrchestrator:
    """
    Orchestrator that works with goal-driven agents.

    Key difference from regular Orchestrator:
      - Agents declare goals, Orchestrator coordinates
      - Orchestrator doesn't control execution flow
      - Orchestrator resolves inter-agent conflicts
      - Orchestrator monitors goal achievement
    """

    def __init__(self, agents: dict[str, GoalDrivenAgent]):
        self.agents = agents
        self.pending_help_requests: list[dict] = []
        self.active_goals: list[Goal] = []
        self.completed_goals: list[Goal] = []

    def coordinate(self, state: WorldState, cognitive_model: CognitiveWorldModel) -> WorldState:
        """
        Coordinate agents through goal-based collaboration.

        This is NOT a task scheduler - it's a coordinator that:
          1. Receives goal declarations from agents
          2. Routes help requests
          3. Resolves conflicts
          4. Monitors overall goal achievement
        """
        # Connect agents to cognitive model
        for agent in self.agents.values():
            agent.set_cognitive_model(cognitive_model)

        # Process pending help requests
        self._process_help_requests()

        # Monitor active goals
        self._monitor_goals()

        return state

    def _process_help_requests(self) -> None:
        """Process pending help requests between agents."""
        resolved = []
        for req in self.pending_help_requests:
            target_agent = self.agents.get(req["to"])
            if target_agent:
                # Route to target agent
                # (In real implementation, this would be async)
                resolved.append(req)

        # Remove resolved requests
        for req in resolved:
            self.pending_help_requests.remove(req)

    def _monitor_goals(self) -> None:
        """Monitor active goals and log status."""
        for goal in self.active_goals:
            if goal.status in (GoalStatus.ACHIEVED, GoalStatus.FAILED, GoalStatus.ABANDONED):
                self.completed_goals.append(goal)
                self.active_goals.remove(goal)

    def get_goal_status(self) -> dict:
        """Get overall goal achievement status."""
        total = len(self.completed_goals) + len(self.active_goals)
        achieved = sum(1 for g in self.completed_goals if g.status == GoalStatus.ACHIEVED)
        failed = sum(1 for g in self.completed_goals if g.status == GoalStatus.FAILED)

        return {
            "total_goals": total,
            "active_goals": len(self.active_goals),
            "completed_goals": len(self.completed_goals),
            "achieved": achieved,
            "failed": failed,
            "success_rate": achieved / max(1, len(self.completed_goals)),
            "pending_requests": len(self.pending_help_requests),
        }
