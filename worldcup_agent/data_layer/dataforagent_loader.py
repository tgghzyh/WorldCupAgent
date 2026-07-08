"""Utilities for reading normalized DataForAgent outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATAFORAGENT_ROOT = PROJECT_ROOT / "DataForAgent"
PROCESSED_ROOT = DATAFORAGENT_ROOT / "data" / "processed"
PROCESSED_INDEX = PROCESSED_ROOT / "index.json"


class DataForAgentError(RuntimeError):
    """Raised when a DataForAgent dataset cannot be loaded."""


def load_processed_index(index_path: Path | None = None) -> dict[str, Any]:
    """Load the DataForAgent processed dataset index."""

    path = index_path or PROCESSED_INDEX
    try:
        with path.open("r", encoding="utf-8") as f:
            index = json.load(f)
    except FileNotFoundError as exc:
        raise DataForAgentError(f"DataForAgent index not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DataForAgentError(f"DataForAgent index is not valid JSON: {path}") from exc

    if not isinstance(index, dict) or not isinstance(index.get("datasets"), dict):
        raise DataForAgentError("DataForAgent index must contain a datasets object")

    return index


def resolve_dataset_path(
    dataset_key: str,
    index: dict[str, Any] | None = None,
) -> Path:
    """Resolve a dataset key from the processed index to an absolute file path."""

    data_index = index or load_processed_index()
    datasets = data_index["datasets"]
    if dataset_key not in datasets:
        available = ", ".join(sorted(datasets))
        raise DataForAgentError(
            f"Unknown DataForAgent dataset '{dataset_key}'. Available: {available}"
        )

    dataset = datasets[dataset_key]
    if not isinstance(dataset, dict) or not isinstance(dataset.get("file"), str):
        raise DataForAgentError(
            f"DataForAgent dataset '{dataset_key}' must contain a file string"
        )

    path = DATAFORAGENT_ROOT / "data" / dataset["file"]
    if not path.exists():
        raise DataForAgentError(
            f"DataForAgent dataset file not found for '{dataset_key}': {path}"
        )

    return path


def load_dataset(dataset_key: str) -> Any:
    """Load one processed DataForAgent dataset by key."""

    path = resolve_dataset_path(dataset_key)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_all_processed_datasets() -> dict[str, Any]:
    """Load all datasets listed in the DataForAgent processed index."""

    index = load_processed_index()
    return {key: load_dataset(key) for key in index["datasets"]}
