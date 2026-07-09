"""LLM-first prediction layer for the WC2026 agent."""

from worldcup_agent.llm_agent.snapshot_writer import (
    LLMSnapshotUpdateResult,
    update_snapshot_with_llm_predictions,
)

__all__ = [
    "LLMSnapshotUpdateResult",
    "update_snapshot_with_llm_predictions",
]
