"""WC2026 Multi-Agent System.

This module implements an advanced multi-agent system with:
  1. ReAct-style reasoning in each agent
  2. Shared World State for inter-agent communication
  3. Orchestrator as planner/scheduler (not controller)
  4. Monte Carlo simulation for tournament prediction
  5. Reflection agent for self-correction
  6. Cognitive World Model with Belief-Uncertainty-Evidence
  7. Goal-Driven Agent autonomy
  8. Debate Mechanism for adversarial collaboration

Key principles:
  - Each agent has its own observe → think → act → evaluate → revise loop
  - Agents communicate through Shared World State
  - Orchestrator decides WHAT to do, agents decide HOW to do it
  - Failure detection → re-planning → re-execution loop
  - Cognitive model enables explainability
  - Debate mechanism enables multi-perspective validation

Usage:
  from worldcup_agent.multi_agent import WC2026MultiAgent
  system = WC2026MultiAgent()
  result = system.run_full_pipeline()
"""
from worldcup_agent.multi_agent.core import (
    WorldState,
    TaskType,
    AgentStatus,
    AgentTrace,
    AgentMessage,
    BaseAgent,
    Orchestrator,
    WC2026AgentSystem,
    ReActStep,
    StepStatus,
)
from worldcup_agent.multi_agent.main import WC2026MultiAgent, PipelineResult
from worldcup_agent.multi_agent.cognitive_model import (
    CognitiveWorldModel,
    Belief,
    Evidence,
    EvidenceChain,
    EvidenceSource,
    EvidenceQuality,
    UncertaintyType,
    ConflictRecord,
)
from worldcup_agent.multi_agent.goal_agent import (
    GoalDrivenAgent,
    Goal,
    GoalType,
    GoalStatus,
    AgentDecision,
    DecisionType,
    GoalDrivenOrchestrator,
)
from worldcup_agent.multi_agent.debate_mechanism import (
    DebateManager,
    Debate,
    DebateRound,
    DebateStatus,
    Argument,
    PositionSide,
    ArgumentStrength,
)

__all__ = [
    # Core types
    "WorldState",
    "TaskType",
    "AgentStatus",
    "AgentTrace",
    "AgentMessage",
    "ReActStep",
    "StepStatus",
    # Base classes
    "BaseAgent",
    # Orchestrator
    "Orchestrator",
    "WC2026AgentSystem",
    # Main entry point
    "WC2026MultiAgent",
    "PipelineResult",
    # Cognitive Model
    "CognitiveWorldModel",
    "Belief",
    "Evidence",
    "EvidenceChain",
    "EvidenceSource",
    "EvidenceQuality",
    "UncertaintyType",
    "ConflictRecord",
    # Goal-Driven Agent
    "GoalDrivenAgent",
    "Goal",
    "GoalType",
    "GoalStatus",
    "AgentDecision",
    "DecisionType",
    "GoalDrivenOrchestrator",
    # Debate Mechanism
    "DebateManager",
    "Debate",
    "DebateRound",
    "DebateStatus",
    "Argument",
    "PositionSide",
    "ArgumentStrength",
]
