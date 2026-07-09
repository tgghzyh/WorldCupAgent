"""Update the canonical snapshot with DataForAgent-driven LLM predictions."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from worldcup_agent.llm_agent.context_builder import DataForAgentContextBuilder, SNAPSHOT_PATH
from worldcup_agent.llm_agent.llm_client import create_chat_client
from worldcup_agent.llm_agent.predictor import LLMMatchPredictor, MatchPrediction, PROMPT_VERSION
from worldcup_agent.llm_agent.snapshot_builder import (
    build_final_and_third_place,
    build_knockout_from_group_tables,
    build_next_round,
    rebuild_snapshot_from_squad,
    refresh_champion_probabilities,
)


@dataclass
class LLMSnapshotUpdateResult:
    snapshot_path: Path
    matches_updated: int
    provider: str
    model: str
    duration_ms: int


def update_snapshot_with_llm_predictions(
    *,
    snapshot_path: Path = SNAPSHOT_PATH,
    require_llm: bool = False,
    match_limit: int | None = None,
) -> LLMSnapshotUpdateResult:
    """Rebuild the tournament from DataForAgent and predict matches in bracket order."""

    started = time.time()
    builder = DataForAgentContextBuilder(snapshot_path=snapshot_path)
    rebuild_snapshot_from_squad(builder.snapshot, builder.squad)

    client = create_chat_client()
    predictor = LLMMatchPredictor(client, require_llm=require_llm)
    provider = client.provider if client else "no_api_key_fallback"
    model = client.model if client else "deterministic_context_fallback"
    request_delay_seconds = _env_float("LLM_REQUEST_DELAY_SECONDS", 0.8) if client else 0.0

    updated = 0
    limit_reached = False

    try:
        group_matches = [
            match
            for group in builder.snapshot.get("group_predictions", {}).values()
            for match in group.get("matches", [])
        ]
        updated, limit_reached = _predict_match_batch(
            builder,
            predictor,
            group_matches,
            "group",
            updated,
            match_limit,
            request_delay_seconds,
        )

        _recalculate_group_tables(builder.snapshot)
        build_knockout_from_group_tables(builder.snapshot)

        if not limit_reached:
            rounds = builder.snapshot["knockout_predictions"]["rounds"]
            updated, limit_reached = _predict_match_batch(
                builder,
                predictor,
                rounds["round_of_32"],
                "knockout",
                updated,
                match_limit,
                request_delay_seconds,
            )

        if not limit_reached:
            build_next_round(builder.snapshot, "round_of_32", "round_of_16")
            rounds = builder.snapshot["knockout_predictions"]["rounds"]
            updated, limit_reached = _predict_match_batch(
                builder,
                predictor,
                rounds["round_of_16"],
                "knockout",
                updated,
                match_limit,
                request_delay_seconds,
            )

        if not limit_reached:
            build_next_round(builder.snapshot, "round_of_16", "quarter_finals")
            rounds = builder.snapshot["knockout_predictions"]["rounds"]
            updated, limit_reached = _predict_match_batch(
                builder,
                predictor,
                rounds["quarter_finals"],
                "knockout",
                updated,
                match_limit,
                request_delay_seconds,
            )

        if not limit_reached:
            build_next_round(builder.snapshot, "quarter_finals", "semi_finals")
            rounds = builder.snapshot["knockout_predictions"]["rounds"]
            updated, limit_reached = _predict_match_batch(
                builder,
                predictor,
                rounds["semi_finals"],
                "knockout",
                updated,
                match_limit,
                request_delay_seconds,
            )

        if not limit_reached:
            build_final_and_third_place(builder.snapshot)
            rounds = builder.snapshot["knockout_predictions"]["rounds"]
            updated, limit_reached = _predict_match_batch(
                builder,
                predictor,
                [rounds["third_place"], rounds["final"]],
                "knockout",
                updated,
                match_limit,
                request_delay_seconds,
            )
    except Exception:
        _append_reasoning_entry(
            builder.snapshot,
            updated,
            provider,
            model,
            int((time.time() - started) * 1000),
            status="partial_failure",
        )
        _write_snapshot(snapshot_path, builder.snapshot)
        raise

    _recalculate_group_tables(builder.snapshot)
    _refresh_champion_fields(builder.snapshot)
    refresh_champion_probabilities(builder.snapshot)
    _append_reasoning_entry(
        builder.snapshot,
        updated,
        provider,
        model,
        int((time.time() - started) * 1000),
        status="partial" if limit_reached else "success",
    )

    now = datetime.utcnow()
    builder.snapshot["snapshot_time"] = now.isoformat()
    builder.snapshot["expires_at"] = (now + timedelta(hours=12)).isoformat()
    current_version = str(builder.snapshot.get("prediction_version", "p"))
    while current_version.endswith("_llm"):
        current_version = current_version[:-4]
    builder.snapshot["prediction_version"] = f"{current_version}_llm"
    builder.snapshot["created_by"] = "WorldCupAgent LLM-first pipeline"
    builder.snapshot["llm_analysis"] = (
        "Snapshot rebuilt from DataForAgent wc_2026_squad_normalized.json. "
        "The LLM-first layer predicts each match with squad, coach, player, ranking, and venue context."
    )

    _write_snapshot(snapshot_path, builder.snapshot)

    return LLMSnapshotUpdateResult(
        snapshot_path=snapshot_path,
        matches_updated=updated,
        provider=provider,
        model=model,
        duration_ms=int((time.time() - started) * 1000),
    )


def _predict_match_batch(
    builder: DataForAgentContextBuilder,
    predictor: LLMMatchPredictor,
    matches: list[dict[str, Any]],
    match_kind: str,
    updated: int,
    match_limit: int | None,
    request_delay_seconds: float,
) -> tuple[int, bool]:
    for index, match in enumerate(matches):
        if match_limit is not None and updated >= match_limit:
            return updated, True
        prediction = predictor.predict(builder._context_for(match))
        _apply_prediction(match, match_kind, prediction)
        updated += 1
        if request_delay_seconds > 0 and index < len(matches) - 1:
            time.sleep(request_delay_seconds)
    return updated, False


def _apply_prediction(match: dict[str, Any], match_kind: str, prediction: MatchPrediction) -> None:
    match.update(prediction.as_snapshot_update())
    home = match.get("home_team")
    away = match.get("away_team")
    winner = home if prediction.winner == "home" else away if prediction.winner == "away" else "Draw"
    loser = away if winner == home else home if winner == away else "Draw"

    match["winner"] = winner
    if match_kind == "knockout":
        match["loser"] = loser


def _parse_score(score: str) -> tuple[int, int]:
    try:
        home, away = score.split("-", 1)
        return int(home.strip()), int(away.strip())
    except Exception:
        return 1, 1


def _recalculate_group_tables(snapshot: dict[str, Any]) -> None:
    for group in snapshot.get("group_predictions", {}).values():
        teams: dict[str, dict[str, Any]] = {}
        for match in group.get("matches", []):
            home = match.get("home_team")
            away = match.get("away_team")
            if not home or not away:
                continue
            teams.setdefault(home, _blank_standing(home))
            teams.setdefault(away, _blank_standing(away))
            hg, ag = _parse_score(match.get("predicted_score", "1-1"))
            _record_result(teams[home], hg, ag)
            _record_result(teams[away], ag, hg)

        standings = sorted(
            teams.values(),
            key=lambda row: (row["points"], row["goal_diff"], row["goals_for"], row["team"]),
            reverse=True,
        )
        group["standings"] = standings
        group["qualifiers"] = [row["team"] for row in standings[:2]]


def _blank_standing(team: str) -> dict[str, Any]:
    return {
        "team": team,
        "played": 0,
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_diff": 0,
        "points": 0,
    }


def _record_result(row: dict[str, Any], goals_for: int, goals_against: int) -> None:
    row["played"] += 1
    row["goals_for"] += goals_for
    row["goals_against"] += goals_against
    row["goal_diff"] = row["goals_for"] - row["goals_against"]
    if goals_for > goals_against:
        row["won"] += 1
        row["points"] += 3
    elif goals_for == goals_against:
        row["drawn"] += 1
        row["points"] += 1
    else:
        row["lost"] += 1


def _refresh_champion_fields(snapshot: dict[str, Any]) -> None:
    rounds = snapshot.get("knockout_predictions", {}).get("rounds", {})
    final = rounds.get("final", {})
    third_place = rounds.get("third_place", {})
    champion = final.get("winner") or snapshot.get("champion")
    runner_up = final.get("loser") or snapshot.get("runner_up")
    third = third_place.get("winner") or snapshot.get("third_place")
    if champion and champion != "Draw":
        snapshot["champion"] = champion
        snapshot["knockout_predictions"]["predicted_champion"] = champion
    if runner_up and runner_up != "Draw":
        snapshot["runner_up"] = runner_up
    if third and third != "Draw":
        snapshot["third_place"] = third


def _append_reasoning_entry(
    snapshot: dict[str, Any],
    updated: int,
    provider: str,
    model: str,
    duration_ms: int,
    status: str = "success",
) -> None:
    chain = snapshot.setdefault("reasoning_chain", [])
    chain[:] = [
        entry
        for entry in chain
        if entry.get("tool") != "llm_match_prediction_agent"
    ]
    chain.append(
        {
            "tool": "llm_match_prediction_agent",
            "action": "predict_dataforagent_tournament",
            "result": f"{updated} matches predicted with {provider}/{model}",
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "prompt_version": PROMPT_VERSION,
            "status": status,
        }
    )


def _write_snapshot(snapshot_path: Path, snapshot: dict[str, Any]) -> None:
    with snapshot_path.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default
