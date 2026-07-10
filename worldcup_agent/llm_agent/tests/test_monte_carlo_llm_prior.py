import unittest

from worldcup_agent.llm_agent.context_builder import MatchContext
from worldcup_agent.llm_agent.predictor import LLMMatchPredictor


class MonteCarloLLMPriorTest(unittest.TestCase):
    def test_monte_carlo_prior_calibrates_fallback_match_prediction(self) -> None:
        context = MatchContext(
            match_id="M1",
            match_type="knockout",
            stage="round_of_32",
            home_team="Home",
            away_team="Away",
            scheduled_date=None,
            prior_prediction={},
            home_profile={"coach": "Home coach", "key_players": []},
            away_profile={"coach": "Away coach", "key_players": []},
            probability_baseline={
                "home_win_prob": 0.25,
                "draw_prob": 0.20,
                "away_win_prob": 0.55,
            },
            monte_carlo_prior={
                "available": True,
                "llm_prediction_weight": 0.70,
                "home_win_prob": 0.78,
                "draw_prob": 0.10,
                "away_win_prob": 0.12,
            },
            data_sources=[],
        )

        prediction = LLMMatchPredictor(None).predict(context)

        self.assertEqual(prediction.winner, "home")
        self.assertGreater(prediction.home_win_prob, prediction.away_win_prob)
        self.assertEqual(prediction.monte_carlo_prior["llm_prediction_weight"], 0.70)
