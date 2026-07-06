"""WC2026 Multi-Agent System — Agents Package.

This package contains all specialized agents for the WC2026 prediction system.

Agents:
  - DataAgent: Handles data acquisition and freshness
  - AnalysisAgent: Analyzes team strengths and matchups
  - SimulationAgent: Runs Monte Carlo tournament simulation
  - ReflectionAgent: Self-correction and quality assurance
  - ExplainerAgent: Generates natural language explanations
  - QualityAgent: Final quality check before output

Each agent implements the ReAct pattern with:
  - observe() → gather information from World State
  - think() → reason about what to do
  - act() → execute the action
  - evaluate() → check if result is satisfactory
  - revise() → revise approach if needed
"""
from __future__ import annotations

from worldcup_agent.multi_agent.agents.data_agent import DataAgent
from worldcup_agent.multi_agent.agents.analysis_agent import AnalysisAgent
from worldcup_agent.multi_agent.agents.simulation_agent import SimulationAgent
from worldcup_agent.multi_agent.agents.reflection_agent import ReflectionAgent
from worldcup_agent.multi_agent.agents.explainer_agent import ExplainerAgent
from worldcup_agent.multi_agent.agents.quality_agent import QualityAgent

__all__ = [
    "DataAgent",
    "AnalysisAgent",
    "SimulationAgent",
    "ReflectionAgent",
    "ExplainerAgent",
    "QualityAgent",
]
