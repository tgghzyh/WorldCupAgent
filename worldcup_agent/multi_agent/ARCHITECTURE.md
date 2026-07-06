# WC2026 Multi-Agent System Architecture (Advanced)

## Overview

This document describes the advanced architecture of the WC2026 Multi-Agent Prediction System, which implements a true multi-agent system with cognitive modeling, goal-driven autonomy, and adversarial collaboration.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         WC2026 Advanced Multi-Agent System                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Cognitive World Model                                │  │
│  │                                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │  │
│  │  │   Belief    │  │  Uncertainty │  │      Evidence Chain        │ │  │
│  │  │             │  │             │  │                             │ │  │
│  │  │ subject     │  │ epistemic   │  │  Agent A → Evidence → Belief│ │  │
│  │  │ predicate   │  │ aleatoric   │  │  Agent B → Evidence → ...  │ │  │
│  │  │ value       │  │ model       │  │  Agent C → Evidence → ...  │ │  │
│  │  │ confidence  │  │             │  │                             │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │  │
│  │                                                                       │  │
│  │  + Conflict Detection + Resolution + Confidence Propagation            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    ▲                                       │
│                                    │                                       │
│  ┌────────────────────────────────┼──────────────────────────────────────┐  │
│  │                         Orchestrator                                  │  │
│  │                                                                       │  │
│  │  • Plan WHAT to achieve (goals, not tasks)                          │  │
│  │  • Coordinate debates                                                │  │
│  │  • Monitor goal achievement                                         │  │
│  │  • NO control over HOW agents execute                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                       │
│         ┌─────────────────────────┼─────────────────────────┐              │
│         │                         │                         │              │
│         ▼                         ▼                         ▼              │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐          │
│  │  Simulation    │    │   Analysis    │    │   Reflection   │          │
│  │    Agent       │◄──►│    Agent       │◄──►│    Agent       │          │
│  │                │    │                │    │                │          │
│  │ Goal-Driven    │    │ Goal-Driven    │    │ Goal-Driven    │          │
│  │ + Debate       │    │ + Debate       │    │ + Judge        │          │
│  └────────────────┘    └────────────────┘    └────────────────┘          │
│         │                         │                         │              │
│         │                         │                         │              │
│         └─────────────────────────┼─────────────────────────┘              │
│                                   ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Debate Mechanism                                   │  │
│  │                                                                       │  │
│  │   Simulation ──► ARGUMENT ─────────────────────────► VERDICT         │  │
│  │                       │                                              │  │
│  │   Analysis  ─────────┼──► REBUTTAL ─────────────────► WINNER       │  │
│  │                       │                                              │  │
│  │              ┌────────┴────────┐                                     │  │
│  │              │  Debate Manager  │                                     │  │
│  │              │                 │                                     │  │
│  │              │  Round 1: Open  │                                     │  │
│  │              │  Round 2: Rebut │                                     │  │
│  │              │  Round 3: Final │                                     │  │
│  │              └─────────────────┘                                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Three-Layer Architecture

### Layer 1: Cognitive World Model

The **Cognitive World Model** is the brain of the system, upgrading the simple WorldState into a proper belief model.

```python
class CognitiveWorldModel:
    def assert_belief(self, subject, predicate, value, evidence, confidence):
        # "I believe X with confidence Y because of evidence Z"
        ...

    def explain_belief(self, subject, predicate):
        # "Why did you predict X?"
        # Returns full evidence chain and reasoning
        ...
```

**Key Capabilities:**

1. **Belief Representation**
   - Explicit subject-predicate-value structure
   - Confidence scores (0-1)
   - Evidence chains

2. **Uncertainty Quantification**
   - Epistemic uncertainty (lack of knowledge)
   - Aleatoric uncertainty (inherent randomness)
   - Model uncertainty

3. **Evidence Management**
   - Source tracking (ELO, simulation, expert opinion)
   - Quality assessment (HIGH/MEDIUM/LOW)
   - Weight in final confidence

4. **Confidence Propagation**
   - Evidence flows through reasoning chain
   - Uncertainty compounds
   - Can trace "why" questions

---

### Layer 2: Goal-Driven Agent Autonomy

The **Goal-Driven Agent** framework transforms agents from passive task executors to autonomous goal seekers.

```python
class GoalDrivenAgent:
    def declare_goal(self, goal_type, description, success_criteria):
        # "I want to achieve X"
        ...

    def decide(self, result, state, goal):
        # "Should I retry? Request help? Escalate?"
        # Agent decides autonomously
        ...
```

**Key Capabilities:**

1. **Goal Declaration**
   - Agents declare goals, not just receive tasks
   - Success criteria defined by agent
   - Hierarchical goals supported

2. **Self-Assessment**
   - Agents evaluate own success
   - Progress tracking
   - Partial success handling

3. **Autonomous Decision Making**
   - CONTINUE: Keep going
   - RETRY: Try different approach
   - REQUEST_INFO: Need more data
   - REQUEST_HELP: Ask other agent
   - ESCALATE: Bring to human/Orchestrator
   - REFINE_GOAL: Adjust goal

4. **Collaboration**
   - Request help from other agents
   - Receive and integrate help
   - Agent-to-agent communication

---

### Layer 3: Debate Mechanism

The **Debate Mechanism** enables adversarial collaboration between agents.

```python
class DebateManager:
    def initiate_debate(self, topic, proponent, opponent):
        # Start debate on a prediction
        ...

    def submit_argument(self, debate_id, agent_id, claim, evidence, reasoning):
        # Make your case
        ...

    def judge_debate(self, debate_id):
        # Reflection Agent judges
        # Returns verdict with confidence
        ...
```

**Key Capabilities:**

1. **Conflict Detection**
   - When beliefs diverge >10%
   - When confidence is low
   - When evidence conflicts

2. **Structured Debate**
   - Round 1: Opening arguments
   - Round 2: Rebuttals
   - Round 3: (Optional) Surrebuttals

3. **Argument Quality**
   - Claim + Evidence + Reasoning
   - Confidence scoring
   - Rebuttal effectiveness

4. **Verdict Generation**
   - Weighted scoring
   - Winner determination
   - Reasoning explanation

---

## Execution Flow

### New Pipeline: With Debate

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Enhanced PREDICT_TOURNAMENT Flow                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Orchestrator                                                              │
│      │                                                                     │
│      ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Phase 1: Goal Declaration                          │    │
│  │                                                                       │    │
│  │  Simulation Agent ──► Goal: "Achieve champion prediction"           │    │
│  │  Analysis Agent ───► Goal: "Analyze team strengths"                │    │
│  │  Data Agent ───────► Goal: "Acquire fresh data"                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                     │
│      ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Phase 2: Belief Formation                         │    │
│  │                                                                       │    │
│  │  Agent asserts belief:                                              │    │
│  │    "Argentina champion = 25%"                                       │    │
│  │    confidence = 0.72                                              │    │
│  │    evidence = [ELO, Simulation, Form]                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                     │
│      ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Phase 3: Conflict Detection                       │    │
│  │                                                                       │    │
│  │  DebateManager detects:                                             │    │
│  │    Simulation: Argentina 25%                                        │    │
│  │    Analysis:   Argentina 30% (divergence!)                          │    │
│  │                                                                       │    │
│  │  → Initiate Debate                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                     │
│      ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Phase 4: Structured Debate                         │    │
│  │                                                                       │    │
│  │  Round 1:                                                           │    │
│  │    Simulation Agent: "25% because Monte Carlo 10K runs"            │    │
│  │    Analysis Agent:   "30% because recent form + Elo gap"            │    │
│  │                                                                       │    │
│  │  Round 2:                                                           │    │
│  │    Simulation Agent: "Rebuttal: MC is more reliable"              │    │
│  │    Analysis Agent:   "Rebuttal: Form matters more"                 │    │
│  │                                                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                     │
│      ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Phase 5: Verdict & Update                         │    │
│  │                                                                       │    │
│  │  Reflection Agent (Judge):                                          │    │
│  │    "VERDICT: Simulation wins (more evidence, higher confidence)"    │    │
│  │    "Final: Argentina 25%, verified = true"                          │    │
│  │                                                                       │    │
│  │  Update Cognitive Model:                                            │    │
│  │    Belief updated, is_verified = true                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│      │                                                                     │
│      ▼                                                                     │
│  Output: Beliefs with evidence chains, verified by debate                   │
│                                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Improvements Over Basic Multi-Agent

| Aspect | Basic Multi-Agent | Advanced (This System) |
|--------|-------------------|------------------------|
| **World State** | Data repository | Cognitive belief model |
| **Reasoning** | Internal ReAct only | ReAct + Evidence chains |
| **Uncertainty** | Implicit | Explicit (epistemic + aleatoric) |
| **Explainability** | Limited | Full "why" with evidence |
| **Agent Control** | Orchestrator-driven | Goal-driven autonomy |
| **Decision Making** | Follow tasks | Autonomous (retry, escalate, etc.) |
| **Conflict Resolution** | Last-write-wins | Structured debate |
| **Prediction Quality** | Single perspective | Multi-perspective validation |

---

## Files Structure

```
WorldCupAgent/
├── worldcup_agent/
│   ├── multi_agent/
│   │   ├── __init__.py              # Core types and exports
│   │   ├── main.py                  # Main entry point
│   │   ├── ARCHITECTURE.md          # This file
│   │   ├── cognitive_model.py       # Belief-Uncertainty-Evidence model
│   │   ├── goal_agent.py            # Goal-driven agent framework
│   │   ├── debate_mechanism.py      # Structured debate system
│   │   └── agents/
│   │       ├── data_agent.py
│   │       ├── analysis_agent.py
│   │       ├── simulation_agent.py
│   │       ├── reflection_agent.py
│   │       ├── explainer_agent.py
│   │       └── quality_agent.py
│   │
│   └── prediction/                  # Original single-agent system
│       └── agent.py
```

---

## Usage

### With Cognitive Model and Debate

```python
from worldcup_agent.multi_agent import (
    WC2026MultiAgent,
    CognitiveWorldModel,
    DebateManager,
    DebateStatus,
)

# Initialize system with cognitive capabilities
system = WC2026MultiAgent()

# Access cognitive model
cognitive = system.cognitive_model

# Assert a belief
cognitive.assert_belief(
    subject="argentina_vs_france",
    predicate="home_win_prob",
    value=0.55,
    confidence=0.72,
    evidence=[...],
    agent_id="simulation_agent",
)

# Explain a prediction
explanation = cognitive.explain_belief("argentina_vs_france", "home_win_prob")
print(explanation["confidence_breakdown"])

# Run with debate
debate_manager = DebateManager(cognitive)
debate = debate_manager.debate_prediction(
    subject="argentina_champion",
    predicate="prob",
    proponent="simulation_agent",
    opponent="analysis_agent",
    pro_value=0.25,
    con_value=0.30,
)
debate_manager.judge_debate(debate.id)
```

### Goal-Driven Execution

```python
from worldcup_agent.multi_agent import GoalDrivenAgent, GoalType

agent = GoalDrivenAgent(name="analysis")

# Declare goal
goal = agent.declare_goal(
    goal_type=GoalType.PREDICT,
    description="Predict Argentina champion probability",
    success_criteria=["confidence_above_0.7", "has_evidence"],
)

# Execute with autonomous decision making
result = agent.run_goal(goal, state)

# Agent autonomously decides: continue? retry? request help?
```

---

## System Properties

### Autonomy Level

| Component | Autonomy Level |
|-----------|----------------|
| Orchestrator | High (decides WHAT, not HOW) |
| GoalDrivenAgent | High (declares goals, self-assesses) |
| BaseAgent | Medium (follows ReAct but fixed) |
| Cognitive Model | Reactive (responds to queries) |
| Debate Manager | Reactive (manages debates when triggered) |

### Explainability

The system can now answer:

1. **"Why did you predict X?"**
   - Trace evidence chain through Cognitive Model
   - Shows all agents that contributed

2. **"How confident are you?"**
   - Confidence score with breakdown
   - Evidence weights

3. **"What could change your mind?"**
   - Uncertain beliefs (confidence < 0.6)
   - Contested beliefs (in debate)
   - Evidence gaps

4. **"Who disagrees?"**
   - Active debates
   - Conflict records
   - Winner/loser verdicts

---

## Summary

This advanced architecture achieves:

1. **Cognitive Modeling**: Beliefs with evidence, uncertainty, and explanation
2. **Goal-Driven Autonomy**: Agents declare goals and self-assess
3. **Adversarial Collaboration**: Structured debate resolves conflicts
4. **Full Explainability**: Every prediction traced through evidence chains

This transforms the system from a "prediction system" to a "reasoning system with verifiable predictions."
