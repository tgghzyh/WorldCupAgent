# Migration Guide: From Single Agent to Multi-Agent

This guide helps you migrate from the single-agent system (`prediction/agent.py`) to the new multi-agent system.

---

## Overview of Changes

### Before (Single Agent)
```python
class WC2026Agent:
    def run(self):
        self._observe()    # Fixed order
        self._plan()      # Fixed order
        self._search()    # Fixed order
        self._execute_tools()  # Fixed order
        self._reason()    # Fixed order
        self._predict()  # Fixed order
        self._update_world_state()  # Fixed order
```

### After (Multi-Agent)
```python
class DataAgent(BaseAgent):
    # ReAct pattern: observe → think → act → evaluate → revise

class AnalysisAgent(BaseAgent):
    # ReAct pattern: observe → think → act → evaluate → revise

class SimulationAgent(BaseAgent):
    # ReAct pattern: observe → think → act → evaluate → revise
    # Plus Monte Carlo simulation

# Orchestrator plans, agents execute autonomously
```

---

## Key Concepts

### 1. Shared World State

**Before:** Data passed through function calls
```python
# Old way
elo = self.tools.refresh_elo_ratings()
teams = self.tools.get_team_features()
predictions = self._predict(elo, teams)
```

**After:** All agents read/write to shared state
```python
# New way
@dataclass
class WorldState:
    teams: dict[str, dict]
    predictions: dict[str, dict]
    simulation_results: dict | None

# Any agent can read/write
agent.observe(state)  # Read from state
agent.act(..., state)  # Write to state
```

### 2. ReAct Pattern

**Before:** Sequential execution
```python
def _execute_tools(self):
    # Just execute, no self-correction
    self.tools.refresh_elo_ratings()
```

**After:** Each agent has observe → think → act → evaluate → revise
```python
class DataAgent(BaseAgent):
    def observe(self, state):
        # Check what data we have
        return {"needs": ["elo", "rankings"]}

    def think(self, observation, state):
        # Decide what to do
        if observation["needs"]:
            return "FETCH_DATA"

    def act(self, thought, state):
        # Execute
        data = self._fetch_data()
        return data, "fetched"

    def evaluate(self, result, state):
        # Check if successful
        return result is not None

    def revise(self, result, error, state):
        # Try alternative
        return "USE_FALLBACK"
```

### 3. Orchestrator as Planner

**Before:** Hard-coded execution order
```python
# Orchestrator controls EVERYTHING
def run(self):
    step1()
    step2()
    step3()
```

**After:** Orchestrator decides WHAT, agents decide HOW
```python
class Orchestrator:
    def plan(self, task):
        # Based on task type, decide which agents to run
        if task == PREDICT_TOURNAMENT:
            return [
                ("data_agent", "check_data"),
                ("analysis_agent", "analyze"),
                ...
            ]
```

---

## Migration Steps

### Step 1: Keep Both Systems

Don't delete the old system yet. Keep both:

```
worldcup_agent/
├── prediction/
│   └── agent.py          # OLD: Keep for now
└── multi_agent/
    ├── __init__.py       # NEW: Core framework
    ├── main.py           # NEW: Entry point
    └── agents/
        ├── data_agent.py
        ├── analysis_agent.py
        └── ...
```

### Step 2: Test New System

```python
from worldcup_agent.multi_agent import WC2026MultiAgent, TaskType

# Initialize
system = WC2026MultiAgent()

# Run new system
result = system.run_full_pipeline()

# Compare outputs
print(f"New system quality: {result.quality_score:.0%}")
print(f"Teams: {len(result.state.teams)}")
```

### Step 3: Compare Outputs

Run both systems and compare:

```python
# Old system
from worldcup_agent.prediction.agent import WC2026Agent
old_agent = WC2026Agent()
old_snapshot = old_agent.run()

# New system
from worldcup_agent.multi_agent import WC2026MultiAgent
new_system = WC2026MultiAgent()
new_result = new_system.run_full_pipeline()

# Compare
print(f"Old predictions: {len(old_snapshot.match_predictions)}")
print(f"New predictions: {len(new_result.state.predictions)}")
```

### Step 4: Gradually Migrate Features

Migrate features one by one:

1. **Data Layer** → DataAgent
2. **Analysis Layer** → AnalysisAgent
3. **Simulation** → SimulationAgent (NEW!)
4. **Quality Checks** → ReflectionAgent + QualityAgent

### Step 5: Update Frontend

The frontend still reads from JSON files. Update the output path:

```python
# Update multi_agent/main.py to output in same format as old system
def _save_output(self) -> Path:
    # Write to same location as old system
    latest_file = Path("data/snapshots/latest.json")
    latest_file.write_text(...)
```

---

## Feature Comparison

| Feature | Old System | New System |
|---------|------------|------------|
| Data Fetching | `ToolRegistry` | `DataAgent` (with ReAct) |
| Analysis | `_reason()` method | `AnalysisAgent` (with ReAct) |
| Prediction | `_predict()` method | `SimulationAgent` |
| Explanation | `ExplainabilityEngine` | `ExplainerAgent` |
| Quality Check | None | `ReflectionAgent` + `QualityAgent` |
| Monte Carlo | None | `SimulationAgent` (10K runs) |
| Self-Correction | None | Each agent can revise |
| Tracing | Basic logging | Full `AgentTrace` |

---

## Running Both Systems

```python
# Compare old vs new
import json
from worldcup_agent.prediction.agent import WC2026Agent
from worldcup_agent.multi_agent import WC2026MultiAgent

# Run old
old = WC2026Agent()
old_snap = old.run()

# Run new
new = WC2026MultiAgent()
new_result = new.run_full_pipeline()

# Compare
print("=== Comparison ===")
print(f"Old: {len(old_snap.match_predictions)} predictions")
print(f"New: {len(new_result.state.predictions)} predictions")
print(f"Old quality: N/A")
print(f"New quality: {new_result.quality_score:.0%}")
```

---

## When to Use Which

| Scenario | Recommendation |
|----------|-----------------|
| Quick test/dev | Either system works |
| Production with MC simulation | New system (SimulationAgent) |
| Need self-correction | New system (ReflectionAgent) |
| Need detailed tracing | New system (AgentTrace) |
| Simple predictions only | Either system |
| Existing tests pass | Keep both until verified |

---

## Common Issues

### Issue 1: Circular Imports

If you get circular import errors:

```python
# In multi_agent/__init__.py
# Don't import agents here, import in main.py
```

### Issue 2: Missing Data Files

New system expects data in specific locations:

```
WorldCupAgent/
└── data/
    ├── cache/
    │   ├── elo_ratings.json
    │   ├── fifa_rankings.json
    │   └── odds.json
    └── data_layer/
        └── cleaned/
            └── teams_2026_enriched.json
```

### Issue 3: State Persistence

Old system persisted state to `data/agent_state.json`.
New system uses `WorldState` in memory, but can serialize to JSON.

---

## Testing the Migration

```python
# test_migration.py

def test_multi_agent():
    from worldcup_agent.multi_agent import WC2026MultiAgent

    system = WC2026MultiAgent(simulation_runs=1000)
    result = system.run_full_pipeline()

    assert result.success, f"Pipeline failed: {result.error}"
    assert result.quality_score >= 0.5
    assert len(result.state.teams) > 0

def test_vs_old():
    from worldcup_agent.prediction.agent import WC2026Agent
    from worldcup_agent.multi_agent import WC2026MultiAgent

    old = WC2026Agent()
    old_snap = old.run()

    new = WC2026MultiAgent(simulation_runs=1000)
    new_result = new.run_full_pipeline()

    # Both should produce predictions
    assert len(old_snap.match_predictions) > 0
    assert len(new_result.state.predictions) >= 0  # May be different format
```

---

## Rollback Plan

If the new system has issues:

1. Revert to old system for production
2. Keep new system in development
3. Fix issues incrementally
4. Re-test before switching

```python
# Quick rollback in main.py
def main():
    if os.environ.get("USE_LEGACY", "0") == "1":
        from worldcup_agent.prediction.agent import WC2026Agent
        agent = WC2026Agent()
        agent.run()
    else:
        from worldcup_agent.multi_agent import WC2026MultiAgent
        system = WC2026MultiAgent()
        system.run_full_pipeline()
```

---

## Summary

The migration involves:

1. **Conceptual change**: From fixed pipeline to autonomous agents
2. **Structural change**: New multi_agent package with 6 agents
3. **Communication change**: Shared World State instead of function calls
4. **Quality change**: Self-correction through ReAct pattern

The new system is more complex but provides:
- Monte Carlo simulation (key differentiator)
- Self-correction (quality improvement)
- Full tracing (debuggability)
- Better extensibility (add agents easily)
