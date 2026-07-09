"""CLI for the LLM-first prediction layer."""

from __future__ import annotations

from pathlib import Path

from worldcup_agent.llm_agent.snapshot_writer import update_snapshot_with_llm_predictions


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Update WC2026 snapshot with LLM match predictions.")
    parser.add_argument("--snapshot", type=Path, default=None, help="Path to latest.json")
    parser.add_argument(
        "--require-llm",
        action="store_true",
        help="Fail if no LLM_API_KEY, OPENAI_API_KEY, or DASHSCOPE_API_KEY is set",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only update the first N matches")
    args = parser.parse_args()

    kwargs = {"require_llm": args.require_llm, "match_limit": args.limit}
    if args.snapshot:
        kwargs["snapshot_path"] = args.snapshot

    result = update_snapshot_with_llm_predictions(**kwargs)
    print(
        "LLM snapshot update complete: "
        f"{result.matches_updated} matches, provider={result.provider}, model={result.model}, "
        f"duration={result.duration_ms}ms"
    )


if __name__ == "__main__":
    main()
