"""Align the canonical champion fields with the deterministic final already in a snapshot."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "snapshots" / "latest.json"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Reconcile canonical champion fields from the predicted final.")
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--sync-frontend", action="store_true")
    args = parser.parse_args()

    with args.snapshot.open("r", encoding="utf-8") as handle:
        snapshot = json.load(handle)

    final = snapshot["knockout_predictions"]["rounds"]["final"]
    champion = final.get("winner")
    if champion not in {final.get("home_team"), final.get("away_team")}:
        raise ValueError("Final winner must be one of the two final teams before reconciliation.")

    raw_probability = final.get("home_win_prob") if champion == final.get("home_team") else final.get("away_win_prob")
    probability = float(str(raw_probability).strip().rstrip("%")) / 100
    snapshot["champion"] = champion
    snapshot["champion_probability"] = round(probability, 4)
    snapshot["runner_up"] = final.get("loser", "")
    knockout = snapshot["knockout_predictions"]
    knockout["predicted_champion"] = champion
    knockout["champion_probability"] = f"{probability * 100:.1f}%"
    snapshot.setdefault("reasoning_chain", []).append(
        {
            "tool": "snapshot_reconciliation_tool",
            "action": "align_canonical_champion_with_deterministic_final",
            "result": f"champion={champion}, final_probability={probability:.1%}",
            "duration_ms": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }
    )

    with args.snapshot.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    if args.sync_frontend:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.sync_snapshot_to_frontend import main as sync_main

        sync_main()

    print(f"Canonical champion reconciled: {champion} ({probability:.1%})")


if __name__ == "__main__":
    main()
