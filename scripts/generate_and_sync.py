"""Run local pipeline checks and sync the frontend snapshot."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "snapshots" / "latest.json"
FRONTEND_SNAPSHOT = ROOT / "frontend" / "public" / "data" / "snapshots" / "latest.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_inputs() -> None:
    from worldcup_agent.data_layer import load_dataset, load_processed_index

    index = load_processed_index()
    for key in index["datasets"]:
        load_dataset(key)

    if not SNAPSHOT.exists():
        raise FileNotFoundError(f"Prediction snapshot not found: {SNAPSHOT}")
    snapshot = _load_json(SNAPSHOT)
    required = ["group_predictions", "knockout_predictions", "champion"]
    missing = [key for key in required if key not in snapshot]
    if missing:
        raise ValueError(f"Snapshot missing required keys: {', '.join(missing)}")

    print(f"Validated DataForAgent datasets: {', '.join(sorted(index['datasets']))}")
    print(
        "Validated prediction snapshot: "
        f"{snapshot.get('prediction_version')} champion={snapshot.get('champion')}"
    )


def run_llm_prediction_layer(
    require_llm: bool = False,
    match_limit: int | None = None,
    skip_reflection: bool = False,
    skip_simulation: bool = False,
    simulation_runs: int | None = None,
) -> None:
    from worldcup_agent.llm_agent import update_snapshot_with_llm_predictions

    result = update_snapshot_with_llm_predictions(
        require_llm=require_llm,
        match_limit=match_limit,
        skip_reflection=skip_reflection,
        skip_simulation=skip_simulation,
        simulation_runs=simulation_runs,
    )
    print(
        "LLM prediction layer: "
        f"{result.teams_profiled} teams profiled, {result.matches_updated} matches updated, "
        f"{result.matches_reflected} matches reflected, {result.simulation_iterations} tournament simulations "
        f"via {result.provider}/{result.model}"
    )


def _is_degenerate_probability_set(probabilities: dict) -> bool:
    if len(probabilities) < 2:
        return True
    values = []
    simulations = 10_000
    for raw in probabilities.values():
        if isinstance(raw, (int, float)):
            values.append(float(raw) / simulations if raw > 1 else float(raw))
        elif isinstance(raw, str) and "(" in raw and raw.endswith("%)"):
            values.append(float(raw.rsplit("(", 1)[1].rstrip("%)")) / 100)
    return bool(values) and max(values) >= 0.995 and sum(1 for value in values if value > 0.001) <= 1


def _allocate_counts(probabilities: dict[str, float], iterations: int) -> dict[str, int]:
    raw_counts = {
        team: max(0.0, probability) * iterations
        for team, probability in probabilities.items()
    }
    counts = {team: int(raw) for team, raw in raw_counts.items()}
    remainder = iterations - sum(counts.values())
    fractions = sorted(
        raw_counts,
        key=lambda team: raw_counts[team] - counts[team],
        reverse=True,
    )

    for team in fractions[:max(0, remainder)]:
        counts[team] += 1

    return counts


def calibrate_snapshot_from_agent_output(output_path: Path | None) -> None:
    """Keep the multi-agent summary observational; it must not overwrite the bracket champion."""

    if not output_path:
        return

    snapshot = _load_json(SNAPSHOT)
    agent_output = _load_json(output_path)
    tournament = (
        agent_output.get("state", {})
        .get("predictions", {})
        .get("tournament", {})
    )
    calibrated = tournament.get("champion_probabilities", {})
    if not calibrated:
        return

    modal_champion = max(calibrated, key=calibrated.get)
    bracket_champion = snapshot.get("champion")
    if modal_champion != bracket_champion:
        print(
            "Multi-agent Monte Carlo modal champion differs from the deterministic bracket projection: "
            f"simulation={modal_champion}, bracket={bracket_champion}. Snapshot left unchanged."
        )


def run_multi_agent() -> Path:
    from worldcup_agent.multi_agent.main import WC2026MultiAgent

    system = WC2026MultiAgent()
    result = system.run_full_pipeline()
    if not result.success:
        raise RuntimeError(result.error or "Multi-agent pipeline failed")
    print(f"Multi-agent output: {result.output_path}")
    return result.output_path


def sync_frontend_snapshot() -> None:
    from scripts.sync_snapshot_to_frontend import main as sync_main

    sync_main()
    _load_json(FRONTEND_SNAPSHOT)


def run_frontend_build() -> None:
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        raise FileNotFoundError(
            "npm was not found on PATH. Install Node.js or run frontend build manually with: "
            "cd frontend && npm run build"
        )

    subprocess.run(
        [npm, "run", "build"],
        cwd=ROOT / "frontend",
        check=True,
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate, run, and sync WC2026 data.")
    parser.add_argument(
        "--skip-agent",
        action="store_true",
        help="Only validate and sync the existing canonical snapshot.",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip the LLM-first match prediction layer.",
    )
    parser.add_argument(
        "--require-llm",
        action="store_true",
        help="Fail if no LLM_API_KEY, OPENAI_API_KEY, or DASHSCOPE_API_KEY is configured.",
    )
    parser.add_argument(
        "--llm-match-limit",
        type=int,
        default=None,
        help="Only update the first N matches through the LLM layer.",
    )
    parser.add_argument(
        "--skip-reflection",
        action="store_true",
        help="Skip the final LLM consistency review; useful for a faster partial run.",
    )
    parser.add_argument(
        "--skip-simulation",
        action="store_true",
        help="Skip Monte Carlo tournament simulation; useful for a faster partial run.",
    )
    parser.add_argument(
        "--simulation-runs",
        type=int,
        default=None,
        help="Number of complete tournament samples; defaults to MONTE_CARLO_RUNS or 10000.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Run frontend production build after syncing.",
    )
    args = parser.parse_args()

    validate_inputs()
    if not args.skip_llm:
        run_llm_prediction_layer(
            require_llm=args.require_llm,
            match_limit=args.llm_match_limit,
            skip_reflection=args.skip_reflection,
            skip_simulation=args.skip_simulation,
            simulation_runs=args.simulation_runs,
        )
    output_path = None
    if not args.skip_agent:
        output_path = run_multi_agent()
        calibrate_snapshot_from_agent_output(output_path)
    sync_frontend_snapshot()
    if args.build:
        run_frontend_build()

    print("Pipeline complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        raise
