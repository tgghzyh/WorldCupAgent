"""Validate and copy the latest prediction snapshot into the frontend public tree."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "snapshots" / "latest.json"
TARGET = ROOT / "frontend" / "public" / "data" / "snapshots" / "latest.json"


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Snapshot not found: {SOURCE}")

    with SOURCE.open("r", encoding="utf-8") as source_file:
        snapshot = json.load(source_file)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with TARGET.open("w", encoding="utf-8") as target_file:
        json.dump(snapshot, target_file, ensure_ascii=False, indent=2)
        target_file.write("\n")

    print(f"Synced {SOURCE.relative_to(ROOT)} -> {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
