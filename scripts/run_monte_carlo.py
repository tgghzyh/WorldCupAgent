"""Re-run the connected Monte Carlo layer without repeating LLM requests."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "snapshots" / "latest.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the connected WC2026 Monte Carlo simulation only.")
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT, help="Canonical snapshot to update")
    parser.add_argument("--runs", type=int, default=None, help="Tournament samples; defaults to 10000")
    parser.add_argument("--seed", type=int, default=None, help="Random seed; defaults to 20260710")
    parser.add_argument("--sync-frontend", action="store_true", help="Copy the updated snapshot to frontend/public")
    args = parser.parse_args()

    from worldcup_agent.llm_agent.monte_carlo import (
        MODEL_VERSION,
        apply_monte_carlo_result,
        run_tournament_monte_carlo,
    )

    with args.snapshot.open("r", encoding="utf-8") as handle:
        snapshot = json.load(handle)

    runs = args.runs or _env_int("MONTE_CARLO_RUNS", int(snapshot.get("monte_carlo_simulations") or 10_000))
    seed = args.seed if args.seed is not None else _env_int("MONTE_CARLO_SEED", 20_260_710)
    started = time.perf_counter()
    result = run_tournament_monte_carlo(snapshot, iterations=runs, seed=seed)
    apply_monte_carlo_result(snapshot, result)

    chain = snapshot.setdefault("reasoning_chain", [])
    chain[:] = [entry for entry in chain if entry.get("tool") != "monte_carlo_tool"]
    chain.append(
        {
            "tool": "monte_carlo_tool",
            "action": "simulate_dataforagent_tournament",
            "result": (
                f"{result.iterations} full tournament samples; "
                f"modal champion={result.champion} ({result.champion_probability:.1%})"
            ),
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "timestamp": datetime.utcnow().isoformat(),
            "prompt_version": MODEL_VERSION,
            "status": "success",
            "requests": 0,
        }
    )
    now = datetime.utcnow()
    snapshot["snapshot_time"] = now.isoformat()
    snapshot["expires_at"] = (now + timedelta(hours=12)).isoformat()
    with args.snapshot.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    if args.sync_frontend:
        from scripts.sync_snapshot_to_frontend import main as sync_main

        sync_main()

    print(
        f"Monte Carlo complete: {result.iterations} samples, "
        f"champion={result.champion}, probability={result.champion_probability:.1%}"
    )


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


if __name__ == "__main__":
    main()
