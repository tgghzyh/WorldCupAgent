"""LLM Reasoning Demo — WC2026 Agent.

This script demonstrates the LLM-powered reasoning capabilities:
1. Match result analysis
2. Prediction explanations
3. Tournament narrative generation

Run:
  python -m worldcup_agent.prediction.demo_llm
"""
from worldcup_agent.prediction.llm_engine import create_llm_engine

def main():
    print("=" * 70)
    print("WC2026 AGENT - LLM REASONING DEMO")
    print("=" * 70)
    print()
    print("This demo shows the LLM-powered reasoning capabilities:")
    print("  1. Match Result Analysis")
    print("  2. Prediction Explanations")
    print("  3. Tournament Summaries")
    print()

    # Create LLM engine
    engine = create_llm_engine()
    print(f"Engine: {type(engine).__name__}")
    if hasattr(engine, 'model'):
        print(f"Model: {engine.model}")
    print()

    # ── Test 1: Match Result Analysis ────────────────────────────────────
    print("=" * 70)
    print("TEST 1: MATCH RESULT ANALYSIS")
    print("=" * 70)
    print()

    matches = [
        ("Argentina", "Brazil", 2, 1),
        ("France", "England", 1, 3),
        ("Germany", "Spain", 0, 0),
        ("Portugal", "Netherlands", 4, 2),
    ]

    for home, away, h_score, a_score in matches:
        print(f"MATCH: {home} {h_score} - {a_score} {away}")
        print("-" * 50)

        result = engine.analyze_match_result(
            home_team=home,
            away_team=away,
            home_score=h_score,
            away_score=a_score,
            world_state_context="Group stage, day 2. Both teams need points to qualify."
        )

        if result.success:
            print(f"[OK] Latency: {result.latency_ms:.0f}ms")
            print()
            print(result.content)
        else:
            print(f"[FAIL] {result.error}")

        print()
        print()

    # ── Test 2: Prediction Explanations ─────────────────────────────────
    print("=" * 70)
    print("TEST 2: PREDICTION EXPLANATIONS")
    print("=" * 70)
    print()

    predictions = [
        ("France", "England", 0.45, 0.25, 0.30),
        ("Germany", "Brazil", 0.35, 0.28, 0.37),
        ("Argentina", "Portugal", 0.55, 0.22, 0.23),
    ]

    for home, away, h_prob, d_prob, a_prob in predictions:
        print(f"PREDICTION: {home} vs {away}")
        print(f"  {home} Win: {h_prob:.0%} | Draw: {d_prob:.0%} | {away} Win: {a_prob:.0%}")
        print("-" * 50)

        result = engine.generate_prediction_explanation(
            home_team=home,
            away_team=away,
            home_win_prob=h_prob,
            draw_prob=d_prob,
            away_win_prob=a_prob,
            factors=[
                {"name": "ELO Rating", "evidence": f"{home} has higher Elo rating"},
                {"name": "Recent Form", "evidence": f"{home} won 3 of last 5 matches"},
            ]
        )

        if result.success:
            print(f"[OK] Latency: {result.latency_ms:.0f}ms")
            print()
            print(result.content)
        else:
            print(f"[FAIL] {result.error}")

        print()
        print()

    # ── Test 3: Tournament Summary ───────────────────────────────────────
    print("=" * 70)
    print("TEST 3: TOURNAMENT SUMMARY")
    print("=" * 70)
    print()

    result = engine.summarize_tournament_state({
        "results": [{"id": i} for i in range(24)],  # 24 matches completed
        "teams": {
            "Argentina": {"stats": {"points": 7, "played": 3, "won": 2, "drawn": 1}},
            "Brazil": {"stats": {"points": 6, "played": 3, "won": 2, "drawn": 0}},
            "France": {"stats": {"points": 5, "played": 3, "won": 1, "drawn": 2}},
            "Germany": {"stats": {"points": 4, "played": 3, "won": 1, "drawn": 1}},
            "England": {"stats": {"points": 7, "played": 3, "won": 2, "drawn": 1}},
        }
    })

    if result.success:
        print(f"[OK] Latency: {result.latency_ms:.0f}ms")
        print()
        print("Daily Briefing:")
        print("-" * 50)
        print(result.content)
    else:
        print(f"[FAIL] {result.error}")

    print()
    print("=" * 70)
    print("LLM REASONING DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
