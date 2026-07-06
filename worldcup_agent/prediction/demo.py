"""Demo: Closed-Loop World Cup Prediction Agent.

This script demonstrates the Agent's closed-loop behavior:
  1. Initial prediction (before any matches)
  2. Simulate match results
  3. Agent observes results and updates predictions
  4. Show how predictions change based on real results

Run:
  python -m worldcup_agent.prediction.demo
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from worldcup_agent.prediction.world_state import (
    WorldState,
    MatchResult,
    TeamState,
    save_world_state,
    load_world_state,
    DATA_DIR,
)
from worldcup_agent.prediction.observer import SimulatedObserver
from worldcup_agent.prediction.agent import WC2026Agent


# ── Sample Elo Map ─────────────────────────────────────────────────────────────

SAMPLE_ELO_MAP = {
    "Argentina": 2151,
    "Brazil": 2134,
    "France": 2128,
    "England": 2095,
    "Germany": 2067,
    "Spain": 2089,
    "Portugal": 2068,
    "Netherlands": 2045,
    "Italy": 2034,
    "Belgium": 2031,
    "Uruguay": 1978,
    "Mexico": 1912,
    "USA": 1890,
    "Croatia": 1967,
    "Japan": 1888,
    "South Korea": 1876,
}


def create_initial_world_state() -> WorldState:
    """Create a fresh WorldState with all teams."""
    state = WorldState()
    state.current_stage = "group"

    for team_name, elo in SAMPLE_ELO_MAP.items():
        group_letter = ["A", "B", "C", "D", "E", "F", "G", "H"][
            list(SAMPLE_ELO_MAP.keys()).index(team_name) % 8
        ]
        state.add_team(team_name, elo=elo, group=f"Group {group_letter}")

    return state


def simulate_group_matches(state: WorldState) -> list[MatchResult]:
    """Simulate some group stage matches."""
    observer = SimulatedObserver(SAMPLE_ELO_MAP)
    results = []

    # Simulate Argentina vs Brazil (Group A - day 1)
    h_score, a_score = observer.simulate_result("Argentina", "Brazil")
    results.append(MatchResult(
        match_id="group_001",
        home_team="Argentina",
        away_team="Brazil",
        home_score=h_score,
        away_score=a_score,
        stage="group",
        kickoff=datetime.now(timezone.utc).isoformat(),
    ))

    # Simulate France vs England (Group B - day 1)
    h_score, a_score = observer.simulate_result("France", "England")
    results.append(MatchResult(
        match_id="group_002",
        home_team="France",
        away_team="England",
        home_score=h_score,
        away_score=a_score,
        stage="group",
        kickoff=datetime.now(timezone.utc).isoformat(),
    ))

    # Simulate Germany vs Spain (Group C - day 1)
    h_score, a_score = observer.simulate_result("Germany", "Spain")
    results.append(MatchResult(
        match_id="group_003",
        home_team="Germany",
        away_team="Spain",
        home_score=h_score,
        away_score=a_score,
        stage="group",
        kickoff=datetime.now(timezone.utc).isoformat(),
    ))

    return results


def main():
    print("=" * 70)
    print("WC2026 CLOSED-LOOP AGENT DEMONSTRATION")
    print("=" * 70)
    print()
    print("This demo shows how the Agent:")
    print("  1. Makes initial predictions")
    print("  2. Observes real match results")
    print("  3. Updates its internal state")
    print("  4. Re-predicts remaining matches with new information")
    print("  5. Explains WHY predictions changed")

    # ── ITERATION 0: Initial State ────────────────────────────────────────
    print()
    print("=" * 70)
    print("ITERATION 0: INITIAL STATE (No real results)")
    print("=" * 70)

    # Reset world state
    state = create_initial_world_state()
    save_world_state(state)

    # Run agent (initial prediction)
    agent = WC2026Agent(verbose=False)
    snapshot = agent.run()

    print()
    print("[OK] Initial predictions generated")
    print(f"     Snapshot: {snapshot.snapshot_id}")
    print(f"     Headline: {snapshot.headline}")
    print()
    print("[NOTE] These predictions are based ONLY on pre-tournament Elo ratings.")
    print("       No real match results have been observed yet.")

    # Show initial prediction for Argentina vs Brazil
    for pred in snapshot.match_predictions:
        if "Argentina" in pred.home_team or "Argentina" in pred.away_team:
            if "Brazil" in pred.home_team or "Brazil" in pred.away_team:
                print()
                print("Initial prediction - Argentina vs Brazil:")
                print(f"  Home Win: {pred.outcome.home_win:.1%} | Draw: {pred.outcome.draw:.1%} | Away Win: {pred.outcome.away_win:.1%}")
                break

    # ── ITERATION 1: After First Match ────────────────────────────────────
    print()
    print("=" * 70)
    print("ITERATION 1: AFTER FIRST MATCHES")
    print("=" * 70)

    # Load world state and add simulated results
    state = load_world_state()
    results = simulate_group_matches(state)

    print()
    print("NEW MATCH RESULTS (simulated):")
    for result in results:
        print(f"  {result.home_team} {result.home_score} - {result.away_score} {result.away_team}")
        if result.winner:
            print(f"    -> {result.winner} wins")
        else:
            print(f"    -> Draw")
        state.add_result(result)

    save_world_state(state)

    # Run agent again (should observe results and update predictions)
    print()
    print("[RUNNING] Agent observing new results and updating predictions...")
    agent = WC2026Agent(verbose=False)
    snapshot = agent.run()

    print()
    print("[OK] Updated predictions generated")
    print(f"     Snapshot: {snapshot.snapshot_id}")
    print(f"     Headline: {snapshot.headline}")

    # Show changes
    if snapshot.changes_from_previous:
        print()
        print("PREDICTION CHANGES:")
        for change in snapshot.changes_from_previous[:3]:
            print(f"  {change['teams']}: {change['metric']} "
                  f"{change['prev']:.1%} -> {change['curr']:.1%} "
                  f"({change['direction']}{abs(change['delta_pct']):.1f}pp)")

    # Show updated team form
    print()
    print("UPDATED WORLD STATE (team form after matches):")
    for name, team in state.teams.items():
        if team.played > 0:
            print(f"  {name}: {team.won}W-{team.drawn}D-{team.lost}L "
                  f"(Elo adj: {team.effective_elo():.0f}, mult: {team.strength_multiplier:.2f})")

    # ── Summary ──────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("CLOSED-LOOP AGENT SUMMARY")
    print("=" * 70)
    print()
    print("The Agent now demonstrates TRUE AGENT BEHAVIOR:")
    print()
    print("  1. OBSERVE   <- Watches for new match results")
    print("       |")
    print("       v")
    print("  2. UPDATE    <- Records results, adjusts team strengths")
    print("       |")
    print("       v")
    print("  3. REASON    <- Interprets what the results mean")
    print("       |")
    print("       v")
    print("  4. PREDICT   <- Re-generates predictions with updated knowledge")
    print("       |")
    print("       v")
    print("  5. LOOP      <- Returns to step 1 for next update")
    print()
    print("Key Features:")
    print("  [+] WorldState tracks all tournament progress")
    print("  [+] Team strength updates based on real performance")
    print("  [+] Predictions dynamically adjust")
    print("  [+] Full reasoning trace for explainability")
    print("  [+] Can run continuously during tournament (--loop mode)")

    # Save final state
    print()
    print(f"WorldState saved to: {DATA_DIR / 'agent_state.json'}")
    print(f"Latest snapshot: {DATA_DIR / 'snapshots' / 'latest.json'}")


if __name__ == "__main__":
    main()
