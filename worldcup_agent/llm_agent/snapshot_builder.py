"""Build the canonical tournament snapshot from DataForAgent squad data."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from worldcup_agent.llm_agent.fifa_2026_rules import (
    OFFICIAL_NEXT_ROUND_SPECS,
    build_round_of_32_pairings,
)

GROUP_PAIRINGS = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]


def rebuild_snapshot_from_squad(snapshot: dict[str, Any], squad: dict[str, Any]) -> None:
    """Replace stale teams/groups with DataForAgent's normalized WC2026 squad data."""

    generated_at = squad.get("generated_at") or datetime.utcnow().isoformat()
    snapshot["knowledge_version"] = f"dataforagent_{generated_at}"
    snapshot["teams_snapshot"] = _build_teams_snapshot(squad)
    snapshot["group_predictions"] = _build_group_predictions(squad)
    snapshot["knockout_predictions"] = {
        "predicted_champion": "",
        "champion_probability": "0.0%",
        "rounds": {
            "round_of_32": [],
            "round_of_16": [],
            "quarter_finals": [],
            "semi_finals": [],
            "third_place": _empty_knockout_match("third_place", "Third place", "third_place"),
            "final": _empty_knockout_match("final", "Final", "final"),
        },
        "champion_probabilities": {},
    }
    snapshot["champion"] = ""
    snapshot["runner_up"] = ""
    snapshot["third_place"] = ""
    snapshot["champion_probability"] = 0.0
    snapshot["champion_probabilities"] = {}
    snapshot["team_intelligence"] = {}


def build_knockout_from_group_tables(snapshot: dict[str, Any]) -> None:
    """Build the official FIFA 2026 Round-of-32 bracket from group standings."""

    groups = snapshot.get("group_predictions", {})
    group_tables = {
        group: data.get("standings", [])
        for group, data in groups.items()
    }
    matches = [
        _make_knockout_match(match_id, "Round of 32", "round_of_32", home, away, match_number)
        for match_id, match_number, home, away in build_round_of_32_pairings(group_tables)
    ]

    rounds = snapshot["knockout_predictions"]["rounds"]
    rounds["round_of_32"] = matches
    rounds["round_of_16"] = []
    rounds["quarter_finals"] = []
    rounds["semi_finals"] = []
    rounds["third_place"] = _empty_knockout_match("third_place", "Third place", "third_place")
    rounds["final"] = _empty_knockout_match("final", "Final", "final")


def build_next_round(snapshot: dict[str, Any], previous_key: str, next_key: str) -> None:
    rounds = snapshot["knockout_predictions"]["rounds"]
    stage_label = {
        "round_of_16": "Round of 16",
        "quarter_finals": "Quarter-finals",
        "semi_finals": "Semi-finals",
    }[next_key]
    expected_previous = {
        "round_of_16": "round_of_32",
        "quarter_finals": "round_of_16",
        "semi_finals": "quarter_finals",
    }[next_key]
    if previous_key != expected_previous:
        raise ValueError(f"{next_key} must be built from {expected_previous}, not {previous_key}")

    source_matches = {
        match["id"]: match
        for matches in rounds.values()
        if isinstance(matches, list)
        for match in matches
    }
    matches = []
    for match_id, match_number, home_source, away_source in OFFICIAL_NEXT_ROUND_SPECS[next_key]:
        try:
            home = _winner(source_matches[home_source])
            away = _winner(source_matches[away_source])
        except KeyError as exc:
            raise ValueError(f"Missing official knockout dependency {exc.args[0]!r}") from exc
        matches.append(
            _make_knockout_match(
                match_id,
                stage_label,
                next_key,
                home,
                away,
                match_number,
            )
        )
    rounds[next_key] = matches


def build_final_and_third_place(snapshot: dict[str, Any]) -> None:
    rounds = snapshot["knockout_predictions"]["rounds"]
    semi_finals = rounds.get("semi_finals", [])
    if len(semi_finals) < 2:
        return
    rounds["third_place"] = _make_knockout_match(
        "third_place",
        "Third place",
        "third_place",
        _loser(semi_finals[0]),
        _loser(semi_finals[1]),
        1,
    )
    rounds["final"] = _make_knockout_match(
        "final",
        "Final",
        "final",
        _winner(semi_finals[0]),
        _winner(semi_finals[1]),
        1,
    )


def refresh_champion_probabilities(snapshot: dict[str, Any]) -> None:
    final = snapshot.get("knockout_predictions", {}).get("rounds", {}).get("final", {})
    champion = final.get("winner")
    if not champion or champion == "Draw":
        return
    probability = _winner_probability(final)
    formatted = f"{probability * 100:.1f}%"
    snapshot["champion"] = champion
    snapshot["champion_probability"] = round(probability, 4)
    snapshot["champion_probabilities"] = {champion: 1}
    snapshot["knockout_predictions"]["predicted_champion"] = champion
    snapshot["knockout_predictions"]["champion_probability"] = formatted
    snapshot["knockout_predictions"]["champion_probabilities"] = {champion: formatted}
    snapshot["runner_up"] = final.get("loser", "")
    third = snapshot["knockout_predictions"]["rounds"].get("third_place", {})
    snapshot["third_place"] = third.get("winner", "")


def _build_teams_snapshot(squad: dict[str, Any]) -> dict[str, Any]:
    teams = {}
    for group_name, group in squad.get("squads", {}).items():
        for team, data in group.items():
            teams[team] = {
                "group": _group_letter(group_name),
                "coach": data.get("coach"),
                "player_count": len(data.get("players", [])),
            }
    return teams


def _build_group_predictions(squad: dict[str, Any]) -> dict[str, Any]:
    groups = {}
    base_date = datetime(2026, 6, 11, 16, 0, 0)
    day_offset = 0
    for group_name, group in squad.get("squads", {}).items():
        letter = _group_letter(group_name)
        teams = list(group.keys())
        matches = []
        for index, (home_idx, away_idx) in enumerate(GROUP_PAIRINGS, start=1):
            home = teams[home_idx] if home_idx < len(teams) else "TBD"
            away = teams[away_idx] if away_idx < len(teams) else "TBD"
            matches.append(
                {
                    "id": f"{letter}_match_{index}",
                    "match_type": "group",
                    "home_team": home,
                    "away_team": away,
                    "scheduled_date": (base_date + timedelta(days=day_offset)).isoformat(),
                    "stage": f"Group {letter} Match {index}",
                    "round_number": index,
                    "predicted_score": "1-1",
                    "home_win_prob": "33.3%",
                    "draw_prob": "33.4%",
                    "away_win_prob": "33.3%",
                    "confidence": "Low",
                    "reasoning": "Awaiting LLM prediction from DataForAgent squad context.",
                }
            )
            day_offset += 1
        groups[letter] = {
            "group_name": letter,
            "matches": matches,
            "standings": [_blank_standing(team) for team in teams],
            "qualifiers": teams[:2],
        }
    return groups


def _group_letter(group_name: str) -> str:
    return group_name.replace("组", "").replace("Group", "").strip()


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


def _empty_knockout_match(match_id: str, label: str, stage: str) -> dict[str, Any]:
    return _make_knockout_match(match_id, label, stage, "TBD", "TBD", 1)


def _make_knockout_match(
    match_id: str,
    label: str,
    stage: str,
    home: str,
    away: str,
    round_number: int,
) -> dict[str, Any]:
    return {
        "id": match_id,
        "match_type": "knockout",
        "home_team": home,
        "away_team": away,
        "scheduled_date": datetime(2026, 7, 1, 16, 0, 0).isoformat(),
        "stage": label,
        "round_number": round_number,
        "predicted_score": "1-1",
        "home_win_prob": "33.3%",
        "draw_prob": "33.4%",
        "away_win_prob": "33.3%",
        "winner": "",
        "loser": "",
        "reasoning": "Awaiting LLM knockout prediction.",
        "confidence": "Low",
    }


def _winner(match: dict[str, Any]) -> str:
    winner = match.get("winner")
    if winner and winner != "Draw":
        return winner
    home_goals, away_goals = _parse_score(match.get("predicted_score", "1-1"))
    if home_goals >= away_goals:
        return match.get("home_team", "TBD")
    return match.get("away_team", "TBD")


def _loser(match: dict[str, Any]) -> str:
    winner = _winner(match)
    home = match.get("home_team", "TBD")
    away = match.get("away_team", "TBD")
    return away if winner == home else home


def _winner_probability(match: dict[str, Any]) -> float:
    winner = _winner(match)
    raw = match.get("home_win_prob") if winner == match.get("home_team") else match.get("away_win_prob")
    try:
        return float(str(raw).strip().rstrip("%")) / 100
    except ValueError:
        return 0.5


def _parse_score(score: str) -> tuple[int, int]:
    try:
        home, away = score.split("-", 1)
        return int(home.strip()), int(away.strip())
    except Exception:
        return 1, 1
