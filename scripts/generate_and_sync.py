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

    iterations = int(snapshot.get("monte_carlo_simulations") or 10_000)
    numeric_probabilities: dict[str, float] = {}
    for team, probability in calibrated.items():
        if not isinstance(probability, (int, float)):
            continue
        numeric_probabilities[team] = float(probability)

    if not numeric_probabilities:
        return

    probability_total = sum(numeric_probabilities.values()) or 1.0
    numeric_probabilities = {
        team: probability / probability_total
        for team, probability in numeric_probabilities.items()
    }
    counts = _allocate_counts(numeric_probabilities, iterations)
    formatted = {
        team: f"{count}/{iterations} ({count / iterations * 100:.1f}%)"
        for team, count in counts.items()
    }
    champion, champion_count = max(counts.items(), key=lambda item: item[1])
    snapshot["champion"] = champion
    snapshot["champion_probability"] = round(champion_count / iterations, 4)
    snapshot["champion_probabilities"] = counts
    snapshot["knockout_predictions"]["predicted_champion"] = champion
    snapshot["knockout_predictions"]["champion_probability"] = f"{champion_count / iterations * 100:.1f}%"
    snapshot["knockout_predictions"]["champion_probabilities"] = formatted

    with SNAPSHOT.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("Calibrated degenerate champion probabilities from multi-agent output")


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
        "--build",
        action="store_true",
        help="Run frontend production build after syncing.",
    )
    args = parser.parse_args()

    validate_inputs()
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
