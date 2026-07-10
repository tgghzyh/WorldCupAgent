"""Regression coverage for FIFA 2026 bracket allocation and result normalization."""

from __future__ import annotations

import unittest

from worldcup_agent.llm_agent.fifa_2026_rules import (
    FIFA_2026_THIRD_PLACE_ALLOCATION,
    THIRD_PLACE_COLUMNS,
    build_round_of_32_pairings,
)
from worldcup_agent.llm_agent.predictor import _normalize_result


def _group_tables(selected_third_groups: str) -> dict[str, list[dict[str, object]]]:
    tables: dict[str, list[dict[str, object]]] = {}
    for group in "ABCDEFGHIJKL":
        third_points = 4 if group in selected_third_groups else 0
        tables[group] = [
            {"team": f"1{group}", "points": 9, "goal_diff": 5, "goals_for": 7},
            {"team": f"2{group}", "points": 6, "goal_diff": 2, "goals_for": 5},
            {"team": f"3{group}", "points": third_points, "goal_diff": 0, "goals_for": 3},
            {"team": f"4{group}", "points": 0, "goal_diff": -7, "goals_for": 0},
        ]
    return tables


class FIFA2026RulesTest(unittest.TestCase):
    def test_all_495_official_best_third_combinations_are_complete(self) -> None:
        self.assertEqual(len(FIFA_2026_THIRD_PLACE_ALLOCATION), 495)
        for selected, allocation in FIFA_2026_THIRD_PLACE_ALLOCATION.items():
            self.assertEqual(len(selected), 8)
            self.assertEqual(len(allocation), 8)
            self.assertEqual(set(allocation), set(selected))

    def test_round_of_32_uses_official_match_numbers_and_third_slots(self) -> None:
        pairs = build_round_of_32_pairings(_group_tables("EFGHIJKL"))
        self.assertEqual([number for _, number, _, _ in pairs], list(range(73, 89)))
        pair_by_id = {match_id: (home, away) for match_id, _, home, away in pairs}
        self.assertEqual(pair_by_id["r32_73"], ("2A", "2B"))
        self.assertEqual(pair_by_id["r32_74"], ("1E", "3F"))
        self.assertEqual(pair_by_id["r32_85"], ("1B", "3J"))
        self.assertEqual(pair_by_id["r32_87"], ("1K", "3L"))
        self.assertEqual(set(THIRD_PLACE_COLUMNS), set("ABD EGIKL".replace(" ", "")))

    def test_score_and_winner_are_normalized_together(self) -> None:
        score, winner = _normalize_result("1-0", "away", 0.25, 0.2, 0.55, is_knockout=True)
        self.assertEqual((score, winner), ("1-2", "away"))
        score, winner = _normalize_result("1-1", "draw", 0.6, 0.2, 0.2, is_knockout=True)
        self.assertEqual((score, winner), ("2-1", "home"))


if __name__ == "__main__":
    unittest.main()
