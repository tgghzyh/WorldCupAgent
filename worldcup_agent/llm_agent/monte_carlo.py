"""Monte Carlo tournament simulation driven by team intelligence and match probabilities."""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from worldcup_agent.llm_agent.fifa_2026_rules import (
    OFFICIAL_NEXT_ROUND_SPECS,
    best_third_rows,
    build_round_of_32_pairings,
)
from worldcup_agent.llm_agent.probability_model import build_match_probability


MODEL_VERSION = "dataforagent_llm_hybrid_monte_carlo_v2"
GROUP_STAGE_WEIGHT = 0.70
LLM_MATCH_WEIGHT = 0.30


@dataclass
class MonteCarloResult:
    iterations: int
    seed: int
    champion_counts: Counter[str]
    runner_up_counts: Counter[str]
    third_place_counts: Counter[str]
    group_qualification_counts: Counter[str]
    advancement_counts: dict[str, Counter[str]]

    @property
    def champion(self) -> str:
        return _modal_team(self.champion_counts)

    @property
    def champion_probability(self) -> float:
        return self.champion_counts[self.champion] / self.iterations if self.iterations else 0.0

    def as_snapshot_payload(self) -> dict[str, Any]:
        return {
            "model_version": MODEL_VERSION,
            "iterations": self.iterations,
            "seed": self.seed,
            "modal_champion": self.champion,
            "modal_champion_probability": round(self.champion_probability, 4),
            "inputs": {
                "group_stage_probability_weight": GROUP_STAGE_WEIGHT,
                "llm_match_probability_weight": LLM_MATCH_WEIGHT,
                "group_stage": "DataForAgent team intelligence probability baseline blended with LLM match output",
                "knockout": "DataForAgent team intelligence probability baseline, with known LLM pair predictions blended when available",
            },
            "champion_counts": dict(self.champion_counts.most_common()),
            "champion_probabilities": _probabilities(self.champion_counts, self.iterations),
            "runner_up_probabilities": _probabilities(self.runner_up_counts, self.iterations),
            "third_place_probabilities": _probabilities(self.third_place_counts, self.iterations),
            "group_qualification_probabilities": _probabilities(self.group_qualification_counts, self.iterations),
            "advancement_probabilities": {
                stage: _probabilities(counts, self.iterations)
                for stage, counts in self.advancement_counts.items()
            },
        }


def run_tournament_monte_carlo(
    snapshot: dict[str, Any],
    *,
    iterations: int = 10_000,
    seed: int = 20_260_710,
) -> MonteCarloResult:
    """Sample the complete tournament path repeatedly from current Agent probability inputs."""

    if iterations < 1:
        raise ValueError("Monte Carlo iterations must be positive")

    group_predictions = snapshot.get("group_predictions", {})
    if not group_predictions:
        raise ValueError("Cannot simulate tournament without group_predictions")

    known_probabilities = _known_match_probabilities(snapshot)
    team_intelligence = snapshot.get("team_intelligence", {})
    rng = random.Random(seed)
    champions: Counter[str] = Counter()
    runners_up: Counter[str] = Counter()
    third_places: Counter[str] = Counter()
    group_qualifications: Counter[str] = Counter()
    advancement: dict[str, Counter[str]] = defaultdict(Counter)

    for _ in range(iterations):
        group_tables = _simulate_group_stage(rng, group_predictions, known_probabilities)
        r32 = build_round_of_32_pairings(group_tables)
        for _, _, home, away in r32:
            advancement["round_of_32"][home] += 1
            advancement["round_of_32"][away] += 1
        for table in group_tables.values():
            for row in table[:2]:
                group_qualifications[row["team"]] += 1
        for row in best_third_rows(group_tables):
            group_qualifications[row["team"]] += 1

        r32_winners = {
            match_id: _sample_knockout_winner(rng, home, away, known_probabilities, team_intelligence)
            for match_id, _, home, away in r32
        }
        advancement["round_of_16"].update(r32_winners.values())
        r16_winners = _play_official_round(rng, r32_winners, "round_of_16", known_probabilities, team_intelligence)
        advancement["quarter_finals"].update(r16_winners.values())
        quarter_final_winners = _play_official_round(
            rng,
            r16_winners,
            "quarter_finals",
            known_probabilities,
            team_intelligence,
        )
        advancement["semi_finals"].update(quarter_final_winners.values())
        semi_final_winners = _play_official_round(
            rng,
            quarter_final_winners,
            "semi_finals",
            known_probabilities,
            team_intelligence,
        )
        finalists = list(semi_final_winners.values())
        semi_final_losers = [
            _other_team_for_source(match_id, winner, quarter_final_winners, "semi_finals")
            for match_id, winner in semi_final_winners.items()
        ]
        advancement["final"].update(finalists)

        champion = _sample_knockout_winner(rng, finalists[0], finalists[1], known_probabilities, team_intelligence)
        runner_up = finalists[1] if champion == finalists[0] else finalists[0]
        third_place = _sample_knockout_winner(
            rng,
            semi_final_losers[0],
            semi_final_losers[1],
            known_probabilities,
            team_intelligence,
        )
        champions[champion] += 1
        runners_up[runner_up] += 1
        third_places[third_place] += 1
        advancement["champion"][champion] += 1

    return MonteCarloResult(
        iterations=iterations,
        seed=seed,
        champion_counts=champions,
        runner_up_counts=runners_up,
        third_place_counts=third_places,
        group_qualification_counts=group_qualifications,
        advancement_counts=dict(advancement),
    )


def apply_monte_carlo_result(snapshot: dict[str, Any], result: MonteCarloResult) -> None:
    """Expose uncertainty distributions without replacing the deterministic bracket champion."""

    champion = result.champion
    champion_counts = dict(result.champion_counts.most_common())
    formatted = {
        team: f"{count}/{result.iterations} ({count / result.iterations * 100:.1f}%)"
        for team, count in champion_counts.items()
    }
    snapshot["monte_carlo_simulations"] = result.iterations
    snapshot["simulation"] = result.as_snapshot_payload()
    snapshot["monte_carlo_modal_champion"] = champion
    snapshot["monte_carlo_modal_champion_probability"] = round(result.champion_probability, 4)
    snapshot["champion_probabilities"] = champion_counts

    knockout = snapshot.setdefault("knockout_predictions", {})
    knockout["champion_probabilities"] = formatted


def apply_monte_carlo_llm_prior(
    snapshot: dict[str, Any],
    result: MonteCarloResult,
    *,
    llm_prediction_weight: float,
) -> None:
    """Store a pre-prediction simulation distribution for the match-prediction LLM.

    This artifact is intentionally separate from ``simulation``: the latter is
    the final post-prediction distribution shown in the UI, while this one is
    the baseline-only prior that influenced each LLM fixture decision.
    """

    payload = result.as_snapshot_payload()
    payload.update(
        {
            "role": "pre_prediction_llm_prior",
            "llm_prediction_weight": round(max(0.0, min(1.0, llm_prediction_weight)), 3),
            "description": (
                "Tournament-level Monte Carlo title and advancement probabilities supplied "
                "to the match-prediction LLM before fixture predictions."
            ),
        }
    )
    snapshot["monte_carlo_llm_prior"] = payload


def _simulate_group_stage(
    rng: random.Random,
    groups: dict[str, Any],
    known_probabilities: dict[tuple[str, str], tuple[float, float, float]],
) -> dict[str, list[dict[str, Any]]]:
    tables: dict[str, list[dict[str, Any]]] = {}
    for group_name, group in groups.items():
        rows = {
            row["team"]: _empty_row(row["team"], rng.random())
            for row in group.get("standings", [])
            if row.get("team")
        }
        for match in group.get("matches", []):
            home = match.get("home_team")
            away = match.get("away_team")
            if not home or not away or home not in rows or away not in rows:
                continue
            probabilities = known_probabilities.get((home, away), (0.38, 0.26, 0.36))
            home_goals, away_goals = _sample_group_score(rng, probabilities)
            _record_result(rows[home], home_goals, away_goals)
            _record_result(rows[away], away_goals, home_goals)
        tables[group_name] = sorted(
            rows.values(),
            key=lambda row: (row["points"], row["goal_diff"], row["goals_for"], row["tie_breaker"]),
            reverse=True,
        )
    return tables


def _play_official_round(
    rng: random.Random,
    previous_winners: dict[str, str],
    round_key: str,
    known_probabilities: dict[tuple[str, str], tuple[float, float, float]],
    intelligence: dict[str, Any],
) -> dict[str, str]:
    winners: dict[str, str] = {}
    for match_id, _, home_source, away_source in OFFICIAL_NEXT_ROUND_SPECS[round_key]:
        try:
            home = previous_winners[home_source]
            away = previous_winners[away_source]
        except KeyError as exc:
            raise ValueError(f"Missing official Monte Carlo dependency {exc.args[0]!r}") from exc
        winners[match_id] = _sample_knockout_winner(rng, home, away, known_probabilities, intelligence)
    return winners


def _other_team_for_source(
    match_id: str,
    winner: str,
    previous_winners: dict[str, str],
    round_key: str,
) -> str:
    spec = next(spec for spec in OFFICIAL_NEXT_ROUND_SPECS[round_key] if spec[0] == match_id)
    home = previous_winners[spec[2]]
    away = previous_winners[spec[3]]
    return away if winner == home else home


def _sample_knockout_winner(
    rng: random.Random,
    home: str,
    away: str,
    known_probabilities: dict[tuple[str, str], tuple[float, float, float]],
    intelligence: dict[str, Any],
) -> str:
    home_prob, _, away_prob = _pair_probabilities(home, away, known_probabilities, intelligence)
    total = home_prob + away_prob
    return home if rng.random() < home_prob / total else away


def _pair_probabilities(
    home: str,
    away: str,
    known_probabilities: dict[tuple[str, str], tuple[float, float, float]],
    intelligence: dict[str, Any],
) -> tuple[float, float, float]:
    known = known_probabilities.get((home, away))
    if known:
        return known
    reverse = known_probabilities.get((away, home))
    if reverse:
        return reverse[2], reverse[1], reverse[0]

    home_intelligence = intelligence.get(home, {})
    away_intelligence = intelligence.get(away, {})
    baseline = build_match_probability(
        home,
        away,
        _profile_from_intelligence(home_intelligence),
        _profile_from_intelligence(away_intelligence),
        home_intelligence,
        away_intelligence,
    )
    return (
        float(baseline["home_win_prob"]),
        float(baseline["draw_prob"]),
        float(baseline["away_win_prob"]),
    )


def _known_match_probabilities(snapshot: dict[str, Any]) -> dict[tuple[str, str], tuple[float, float, float]]:
    probabilities: dict[tuple[str, str], tuple[float, float, float]] = {}
    for match in _iter_matches(snapshot):
        home = match.get("home_team")
        away = match.get("away_team")
        if not home or not away or home == "TBD" or away == "TBD":
            continue
        baseline = match.get("probability_model") if isinstance(match.get("probability_model"), dict) else {}
        base = _probability_triplet(baseline, "home_win_prob", "draw_prob", "away_win_prob")
        llm = _probability_triplet(match, "home_win_prob", "draw_prob", "away_win_prob")
        if base and llm:
            probabilities[(home, away)] = _normalize(
                base[0] * GROUP_STAGE_WEIGHT + llm[0] * LLM_MATCH_WEIGHT,
                base[1] * GROUP_STAGE_WEIGHT + llm[1] * LLM_MATCH_WEIGHT,
                base[2] * GROUP_STAGE_WEIGHT + llm[2] * LLM_MATCH_WEIGHT,
            )
        elif base:
            probabilities[(home, away)] = base
        elif llm:
            probabilities[(home, away)] = llm
    return probabilities


def _iter_matches(snapshot: dict[str, Any]):
    for group in snapshot.get("group_predictions", {}).values():
        yield from group.get("matches", [])
    rounds = snapshot.get("knockout_predictions", {}).get("rounds", {})
    for stage in ("round_of_32", "round_of_16", "quarter_finals", "semi_finals"):
        yield from rounds.get(stage, [])
    for stage in ("third_place", "final"):
        match = rounds.get(stage)
        if isinstance(match, dict):
            yield match


def _probability_triplet(source: dict[str, Any], *keys: str) -> tuple[float, float, float] | None:
    values = [_parse_probability(source.get(key)) for key in keys]
    if any(value is None for value in values):
        return None
    return _normalize(*values)  # type: ignore[arg-type]


def _parse_probability(raw: Any) -> float | None:
    try:
        if isinstance(raw, str):
            raw = raw.strip().rstrip("%")
        value = float(raw)
        return value / 100 if value > 1 else value
    except (TypeError, ValueError):
        return None


def _sample_group_score(rng: random.Random, probabilities: tuple[float, float, float]) -> tuple[int, int]:
    outcome = _sample_outcome(rng, probabilities)
    edge = probabilities[0] - probabilities[2]
    home_lambda = max(0.35, min(2.7, 1.32 + edge * 1.15))
    away_lambda = max(0.35, min(2.7, 1.18 - edge * 1.15))
    for _ in range(10):
        home_goals = _sample_poisson(rng, home_lambda)
        away_goals = _sample_poisson(rng, away_lambda)
        if _score_outcome(home_goals, away_goals) == outcome:
            return home_goals, away_goals
    return _fallback_score(rng, outcome)


def _sample_outcome(rng: random.Random, probabilities: tuple[float, float, float]) -> str:
    point = rng.random()
    if point < probabilities[0]:
        return "home"
    if point < probabilities[0] + probabilities[1]:
        return "draw"
    return "away"


def _sample_poisson(rng: random.Random, mean: float) -> int:
    threshold = math.exp(-mean)
    count = 0
    product = 1.0
    while product > threshold:
        count += 1
        product *= rng.random()
    return count - 1


def _fallback_score(rng: random.Random, outcome: str) -> tuple[int, int]:
    if outcome == "draw":
        goals = 1 if rng.random() < 0.68 else 0 if rng.random() < 0.5 else 2
        return goals, goals
    winner_goals = 1 + rng.randrange(3)
    loser_goals = rng.randrange(winner_goals)
    return (winner_goals, loser_goals) if outcome == "home" else (loser_goals, winner_goals)


def _empty_row(team: str, tie_breaker: float) -> dict[str, Any]:
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
        "tie_breaker": tie_breaker,
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


def _score_outcome(home_goals: int, away_goals: int) -> str:
    return "home" if home_goals > away_goals else "away" if away_goals > home_goals else "draw"


def _profile_from_intelligence(intelligence: dict[str, Any]) -> dict[str, Any]:
    ranking = intelligence.get("ranking", {}) if isinstance(intelligence, dict) else {}
    return {
        "fifa_rank": ranking.get("fifa_rank"),
        "elo": ranking.get("elo"),
    }


def _normalize(home: float, draw: float, away: float) -> tuple[float, float, float]:
    values = [max(0.01, home), max(0.01, draw), max(0.01, away)]
    total = sum(values)
    return tuple(value / total for value in values)  # type: ignore[return-value]


def _modal_team(counts: Counter[str]) -> str:
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0] if counts else ""


def _probabilities(counts: Counter[str], iterations: int) -> dict[str, float]:
    return {
        team: round(count / iterations, 4)
        for team, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    }
