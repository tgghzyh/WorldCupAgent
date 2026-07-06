"""Test script for LLM integration.

Run:
  python -m worldcup_agent.prediction.test_llm
"""
from worldcup_agent.prediction.llm_engine import create_llm_engine, LLMEngine

def main():
    print("=" * 60)
    print("LLM Integration Test")
    print("=" * 60)

    # Create engine (will use mock if no API key)
    engine = create_llm_engine()

    print(f"\nEngine type: {type(engine).__name__}")
    print(f"Model: {engine.model if hasattr(engine, 'model') else 'N/A'}")

    # Test 1: Match result analysis
    print("\n" + "-" * 40)
    print("Test 1: Match Result Analysis")
    print("-" * 40)

    result = engine.analyze_match_result(
        home_team="Argentina",
        away_team="Brazil",
        home_score=2,
        away_score=1,
        world_state_context="Both teams in Group A, Argentina needs a draw to qualify"
    )

    print(f"\nResult: {'OK' if result.success else 'FAILED'}")
    if result.success:
        print(f"Latency: {result.latency_ms:.0f}ms")
        print(f"\nAnalysis:\n{result.content}")
    else:
        print(f"Error: {result.error}")

    # Test 2: Prediction explanation
    print("\n" + "-" * 40)
    print("Test 2: Prediction Explanation")
    print("-" * 40)

    result = engine.generate_prediction_explanation(
        home_team="France",
        away_team="England",
        home_win_prob=0.45,
        draw_prob=0.25,
        away_win_prob=0.30,
        factors=[
            {"name": "ELO Rating", "evidence": "France Elo 2128 vs England 2095"},
            {"name": "Home Advantage", "evidence": "Playing in neutral venue"},
        ]
    )

    print(f"\nResult: {'OK' if result.success else 'FAILED'}")
    if result.success:
        print(f"Latency: {result.latency_ms:.0f}ms")
        print(f"\nExplanation:\n{result.content}")
    else:
        print(f"Error: {result.error}")

    # Test 3: Tournament summary
    print("\n" + "-" * 40)
    print("Test 3: Tournament State Summary")
    print("-" * 40)

    result = engine.summarize_tournament_state({
        "results": [{"match_id": "1"}, {"match_id": "2"}, {"match_id": "3"}],
        "teams": {
            "Argentina": {"stats": {"points": 6, "played": 2}},
            "Brazil": {"stats": {"points": 3, "played": 2}},
        }
    })

    print(f"\nResult: {'OK' if result.success else 'FAILED'}")
    if result.success:
        print(f"Latency: {result.latency_ms:.0f}ms")
        print(f"\nSummary:\n{result.content}")
    else:
        print(f"Error: {result.error}")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
