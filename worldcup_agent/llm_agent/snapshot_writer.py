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
from worldcup_agent.llm_agent.monte_carlo import (
    MODEL_VERSION as MONTE_CARLO_MODEL_VERSION,
    apply_monte_carlo_llm_prior,
    apply_monte_carlo_result,
    run_tournament_monte_carlo,
)
from worldcup_agent.llm_agent.predictor import LLMMatchPredictor, MatchPrediction, PROMPT_VERSION
from worldcup_agent.llm_agent.reflection import LLMPredictionReflector, PROMPT_VERSION as REFLECTION_PROMPT_VERSION
from worldcup_agent.llm_agent.snapshot_builder import (
    build_final_and_third_place,
    build_knockout_from_group_tables,
    build_next_round,
    rebuild_snapshot_from_squad,
)
from worldcup_agent.llm_agent.team_intelligence import TeamIntelligenceExtractor, PROMPT_VERSION as TEAM_INTELLIGENCE_PROMPT_VERSION


@dataclass
class LLMSnapshotUpdateResult:
    snapshot_path: Path
    matches_updated: int
    teams_profiled: int
    matches_reflected: int
    simulation_iterations: int
    provider: str
    model: str
    duration_ms: int


def update_snapshot_with_llm_predictions(
    *,
    snapshot_path: Path = SNAPSHOT_PATH,
    require_llm: bool = False,
    match_limit: int | None = None,
    skip_reflection: bool = False,
    skip_simulation: bool = False,
    simulation_runs: int | None = None,
) -> LLMSnapshotUpdateResult:
    """Rebuild the tournament from DataForAgent and predict matches in bracket order."""

    started = time.time()
    builder = DataForAgentContextBuilder(snapshot_path=snapshot_path)
    rebuild_snapshot_from_squad(builder.snapshot, builder.squad)

    client = create_chat_client()
    predictor = LLMMatchPredictor(client, require_llm=require_llm)
    intelligence_extractor = TeamIntelligenceExtractor(client, require_llm=require_llm)
    reflector = LLMPredictionReflector(client, require_llm=require_llm)
    provider = client.provider if client else "no_api_key_fallback"
    model = client.model if client else "deterministic_context_fallback"
    request_delay_seconds = _env_float("LLM_REQUEST_DELAY_SECONDS", 0.8) if client else 0.0

    updated = 0
    teams_profiled = 0
    matches_reflected = 0
    simulation_iterations = 0
    simulation_result = None
    limit_reached = False

    try:
        team_intelligence, team_requests = intelligence_extractor.extract_all(
            builder,
            request_delay_seconds=request_delay_seconds,
        )
        builder.snapshot["team_intelligence"] = team_intelligence
        teams_profiled = len(team_intelligence)
        _append_agent_entry(
            builder.snapshot,
            tool="llm_team_intelligence_agent",
            action="extract_dataforagent_team_features",
            result=f"{teams_profiled} teams profiled with {provider}/{model}",
            duration_ms=int((time.time() - started) * 1000),
            prompt_version=TEAM_INTELLIGENCE_PROMPT_VERSION,
            status="success",
            requests=team_requests,
        )
        _attach_group_probability_baselines(builder)

        configured_runs = simulation_runs or _env_int(
            "MONTE_CARLO_RUNS",
            int(builder.snapshot.get("monte_carlo_simulations") or 10_000),
        )
        if not skip_simulation:
            simulation_started = time.time()
            prior_result = run_tournament_monte_carlo(
                builder.snapshot,
                iterations=configured_runs,
                seed=_env_int("MONTE_CARLO_SEED", 20_260_710),
            )
            llm_weight = _env_float("MONTE_CARLO_LLM_WEIGHT", 0.70)
            apply_monte_carlo_llm_prior(
                builder.snapshot,
                prior_result,
                llm_prediction_weight=llm_weight,
            )
            _append_agent_entry(
                builder.snapshot,
                tool="monte_carlo_llm_prior_tool",
                action="simulate_baseline_tournament_for_llm_prior",
                result=(
                    f"{prior_result.iterations} baseline tournament samples; "
                    f"modal champion={prior_result.champion} ({prior_result.champion_probability:.1%}); "
                    f"LLM probability blend weight={max(0.0, min(1.0, llm_weight)):.0%}"
                ),
                duration_ms=int((time.time() - simulation_started) * 1000),
                prompt_version=MONTE_CARLO_MODEL_VERSION,
                status="success",
                requests=0,
            )
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

        if not limit_reached:
            _validate_prediction_consistency(builder.snapshot)
            _refresh_champion_fields(builder.snapshot)
            _set_canonical_champion_probability(builder.snapshot)

        if not limit_reached and not skip_reflection:
            matches_reflected, reflection_requests = reflector.review_snapshot(
                builder.snapshot,
                request_delay_seconds=request_delay_seconds,
            )
            _append_agent_entry(
                builder.snapshot,
                tool="llm_prediction_reflection_agent",
                action="review_prediction_consistency",
                result=f"{matches_reflected} matches reviewed with {provider}/{model}",
                duration_ms=int((time.time() - started) * 1000),
                prompt_version=REFLECTION_PROMPT_VERSION,
                status="success",
                requests=reflection_requests,
            )

        if not limit_reached and not skip_simulation:
            simulation_started = time.time()
            simulation_result = run_tournament_monte_carlo(
                builder.snapshot,
                iterations=configured_runs,
                seed=_env_int("MONTE_CARLO_SEED", 20_260_710),
            )
            apply_monte_carlo_result(builder.snapshot, simulation_result)
            simulation_iterations = simulation_result.iterations
            _append_agent_entry(
                builder.snapshot,
                tool="monte_carlo_tool",
                action="simulate_dataforagent_tournament",
                result=(
                    f"{simulation_result.iterations} full tournament samples; "
                    f"modal champion={simulation_result.champion} ({simulation_result.champion_probability:.1%})"
                ),
                duration_ms=int((time.time() - simulation_started) * 1000),
                prompt_version=MONTE_CARLO_MODEL_VERSION,
                status="success",
                requests=0,
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
        "A team-intelligence LLM extracts structured features, a deterministic probability model provides "
        "a W/D/L baseline, the prediction LLM explains each fixture, a reflection LLM checks consistency, "
        "and Monte Carlo samples the complete tournament to estimate advancement and title probabilities."
    )

    _write_snapshot(snapshot_path, builder.snapshot)

    return LLMSnapshotUpdateResult(
        snapshot_path=snapshot_path,
        matches_updated=updated,
        teams_profiled=teams_profiled,
        matches_reflected=matches_reflected,
        simulation_iterations=simulation_iterations,
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


def _attach_group_probability_baselines(builder: DataForAgentContextBuilder) -> None:
    """Materialize baseline probabilities before the first Monte Carlo pass."""

    for group in builder.snapshot.get("group_predictions", {}).values():
        for match in group.get("matches", []):
            context = builder._context_for(match)
            match["probability_model"] = context.probability_baseline


def _apply_prediction(match: dict[str, Any], match_kind: str, prediction: MatchPrediction) -> None:
    match.update(prediction.as_snapshot_update())
    home = match.get("home_team")
    away = match.get("away_team")
    home_goals, away_goals = _parse_score(prediction.predicted_score)
    score_winner = "home" if home_goals > away_goals else "away" if away_goals > home_goals else "draw"
    if score_winner != prediction.winner:
        raise ValueError(
            f"Inconsistent prediction for {match.get('id')}: "
            f"score={prediction.predicted_score}, winner={prediction.winner}"
        )
    if match_kind == "knockout" and score_winner == "draw":
        raise ValueError(f"Knockout prediction cannot end drawn: {match.get('id')}")

    winner = home if score_winner == "home" else away if score_winner == "away" else "Draw"
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


def _validate_prediction_consistency(snapshot: dict[str, Any]) -> None:
    """Reject a completed snapshot when scorelines and winners cannot describe one result."""

    matches: list[tuple[str, dict[str, Any]]] = []
    for group in snapshot.get("group_predictions", {}).values():
        matches.extend(("group", match) for match in group.get("matches", []))
    rounds = snapshot.get("knockout_predictions", {}).get("rounds", {})
    for round_key in ("round_of_32", "round_of_16", "quarter_finals", "semi_finals"):
        matches.extend(("knockout", match) for match in rounds.get(round_key, []))
    for round_key in ("third_place", "final"):
        match = rounds.get(round_key)
        if isinstance(match, dict):
            matches.append(("knockout", match))

    errors: list[str] = []
    for match_kind, match in matches:
        home_goals, away_goals = _parse_score(match.get("predicted_score", ""))
        score_winner = "home" if home_goals > away_goals else "away" if away_goals > home_goals else "draw"
        winner = match.get("winner")
        expected = (
            match.get("home_team")
            if score_winner == "home"
            else match.get("away_team")
            if score_winner == "away"
            else "Draw"
        )
        if winner != expected:
            errors.append(f"{match.get('id')}: score={match.get('predicted_score')} winner={winner}")
        if match_kind == "knockout" and score_winner == "draw":
            errors.append(f"{match.get('id')}: knockout draw has no advancing team")

    if errors:
        raise ValueError("Prediction consistency validation failed: " + "; ".join(errors[:5]))


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


def _set_canonical_champion_probability(snapshot: dict[str, Any]) -> None:
    """Keep the site-wide champion aligned with the deterministic final projection."""

    final = snapshot.get("knockout_predictions", {}).get("rounds", {}).get("final", {})
    champion = snapshot.get("champion")
    if not champion or champion == "Draw":
        return
    raw_probability = final.get("home_win_prob") if champion == final.get("home_team") else final.get("away_win_prob")
    try:
        probability = float(str(raw_probability).strip().rstrip("%")) / 100
    except ValueError:
        probability = 0.5
    snapshot["champion_probability"] = round(probability, 4)
    knockout = snapshot["knockout_predictions"]
    knockout["predicted_champion"] = champion
    knockout["champion_probability"] = f"{probability * 100:.1f}%"


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


def _append_agent_entry(
    snapshot: dict[str, Any],
    *,
    tool: str,
    action: str,
    result: str,
    duration_ms: int,
    prompt_version: str,
    status: str,
    requests: int,
) -> None:
    chain = snapshot.setdefault("reasoning_chain", [])
    chain[:] = [entry for entry in chain if entry.get("tool") != tool]
    chain.append(
        {
            "tool": tool,
            "action": action,
            "result": result,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "prompt_version": prompt_version,
            "status": status,
            "requests": requests,
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


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default
