"""Build the canonical tournament snapshot from DataForAgent squad data."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


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


def build_knockout_from_group_tables(snapshot: dict[str, Any]) -> None:
    """Build a 32-team knockout bracket from current group standings."""

    groups = snapshot.get("group_predictions", {})
    group_keys = sorted(groups)
    winners = [groups[key]["standings"][0]["team"] for key in group_keys if groups[key].get("standings")]
    runners = [groups[key]["standings"][1]["team"] for key in group_keys if len(groups[key].get("standings", [])) > 1]
    thirds = [
        groups[key]["standings"][2]
        for key in group_keys
        if len(groups[key].get("standings", [])) > 2
    ]
    best_thirds = [
        row["team"]
        for row in sorted(
            thirds,
            key=lambda row: (row["points"], row["goal_diff"], row["goals_for"], row["team"]),
            reverse=True,
        )[:8]
    ]

    top_seeds = winners + runners[:4]
    lower_seeds = best_thirds + runners[4:]
    lower_seeds = list(reversed(lower_seeds))
    matches = []
    for index in range(16):
        home = top_seeds[index] if index < len(top_seeds) else "TBD"
        away = lower_seeds[index] if index < len(lower_seeds) else "TBD"
        matches.append(_make_knockout_match(f"r32_{index + 1:02d}", "Round of 32", "round_of_32", home, away, index + 1))

    rounds = snapshot["knockout_predictions"]["rounds"]
    rounds["round_of_32"] = matches
    rounds["round_of_16"] = []
    rounds["quarter_finals"] = []
    rounds["semi_finals"] = []
    rounds["third_place"] = _empty_knockout_match("third_place", "Third place", "third_place")
    rounds["final"] = _empty_knockout_match("final", "Final", "final")


def build_next_round(snapshot: dict[str, Any], previous_key: str, next_key: str) -> None:
    rounds = snapshot["knockout_predictions"]["rounds"]
    previous = rounds.get(previous_key, [])
    stage_label = {
        "round_of_16": "Round of 16",
        "quarter_finals": "Quarter-finals",
        "semi_finals": "Semi-finals",
    }[next_key]
    prefix = {
        "round_of_16": "r16",
        "quarter_finals": "qf",
        "semi_finals": "sf",
    }[next_key]

    matches = []
    winners = [_winner(match) for match in previous]
    for index in range(0, len(winners), 2):
        if index + 1 >= len(winners):
            break
        matches.append(
            _make_knockout_match(
                f"{prefix}_{len(matches) + 1:02d}",
                stage_label,
                next_key,
                winners[index],
                winners[index + 1],
                len(matches) + 1,
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
