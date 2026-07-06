"""IE-1 smoke test — verify all four blocks run end-to-end.

2026 FIFA World Cup Official Rules Applied:
- 48 teams in 12 groups of 4
- Top 2 from each group + 8 best thirds qualify for R32
- 104 total matches

Tiebreaker changes (NEW in 2026):
- Head-to-head comparison is now the FIRST tiebreaker
"""
from worldcup_agent.tournament import (
    TournamentRule, GroupStanding,
    R32Builder, ThirdPlaceRanker,
    KnockoutSimulator, EloProbModel,
)

# ── Block 1: RULE ──────────────────────────────────────────────────────────────
rule = TournamentRule.wc2026()
print(f"[RULE] WC {rule.year} | {rule.teams} teams | {rule.groups} groups | "
      f"{rule.third_place_advancers} best thirds qualify")
print(f"[RULE] Total matches: {rule.total_matches()}")
assert rule.total_matches() == 104, f"Expected 104 matches, got {rule.total_matches()}"

# ── Block 2: ENGINE — Third-place ranker ─────────────────────────────────────
# Real 2026 World Cup qualified teams (from Wikipedia)
# Note: This is a simplified test scenario with 2026 teams
standings = [
    # Group A (hosts: Mexico)
    GroupStanding(group="A", rank=1, team="Mexico", points=9, goal_diff=6, goals_for=8, fifa_rank=14,
                  h2h_points=9, h2h_goal_diff=6, h2h_goals=8),
    GroupStanding(group="A", rank=2, team="South Africa", points=4, goal_diff=-1, goals_for=2, fifa_rank=73,
                  h2h_points=4, h2h_goal_diff=-1, h2h_goals=2),
    GroupStanding(group="A", rank=3, team="South Korea", points=3, goal_diff=-1, goals_for=2, fifa_rank=25,
                  h2h_points=3, h2h_goal_diff=-1, h2h_goals=2),
    GroupStanding(group="A", rank=4, team="Czech Republic", points=1, goal_diff=-4, goals_for=2, fifa_rank=40,
                  h2h_points=1, h2h_goal_diff=-4, h2h_goals=2),

    # Group B (hosts: Canada)
    GroupStanding(group="B", rank=1, team="Switzerland", points=7, goal_diff=4, goals_for=7, fifa_rank=19,
                  h2h_points=7, h2h_goal_diff=4, h2h_goals=7),
    GroupStanding(group="B", rank=2, team="Canada", points=4, goal_diff=5, goals_for=8, fifa_rank=30,
                  h2h_points=4, h2h_goal_diff=5, h2h_goals=8),
    GroupStanding(group="B", rank=3, team="Bosnia and Herzegovina", points=4, goal_diff=-1, goals_for=5, fifa_rank=64,
                  h2h_points=4, h2h_goal_diff=-1, h2h_goals=5),
    GroupStanding(group="B", rank=4, team="Qatar", points=1, goal_diff=-8, goals_for=2, fifa_rank=56,
                  h2h_points=1, h2h_goal_diff=-8, h2h_goals=2),

    # Group C
    GroupStanding(group="C", rank=1, team="Brazil", points=7, goal_diff=6, goals_for=7, fifa_rank=6,
                  h2h_points=7, h2h_goal_diff=6, h2h_goals=7),
    GroupStanding(group="C", rank=2, team="Morocco", points=7, goal_diff=3, goals_for=6, fifa_rank=7,
                  h2h_points=7, h2h_goal_diff=3, h2h_goals=6),
    GroupStanding(group="C", rank=3, team="Scotland", points=3, goal_diff=-3, goals_for=1, fifa_rank=42,
                  h2h_points=3, h2h_goal_diff=-3, h2h_goals=1),
    GroupStanding(group="C", rank=4, team="Haiti", points=0, goal_diff=-6, goals_for=2, fifa_rank=83,
                  h2h_points=0, h2h_goal_diff=-6, h2h_goals=2),

    # Group D (hosts: USA)
    GroupStanding(group="D", rank=1, team="United States", points=6, goal_diff=4, goals_for=8, fifa_rank=17,
                  h2h_points=6, h2h_goal_diff=4, h2h_goals=8),
    GroupStanding(group="D", rank=2, team="Australia", points=4, goal_diff=0, goals_for=2, fifa_rank=27,
                  h2h_points=4, h2h_goal_diff=0, h2h_goals=2),
    GroupStanding(group="D", rank=3, team="Paraguay", points=4, goal_diff=-2, goals_for=2, fifa_rank=41,
                  h2h_points=4, h2h_goal_diff=-2, h2h_goals=2),
    GroupStanding(group="D", rank=4, team="Turkey", points=3, goal_diff=-2, goals_for=3, fifa_rank=22,
                  h2h_points=3, h2h_goal_diff=-2, h2h_goals=3),

    # Group E
    GroupStanding(group="E", rank=1, team="Germany", points=6, goal_diff=6, goals_for=10, fifa_rank=10,
                  h2h_points=6, h2h_goal_diff=6, h2h_goals=10),
    GroupStanding(group="E", rank=2, team="Ivory Coast", points=6, goal_diff=2, goals_for=4, fifa_rank=33,
                  h2h_points=6, h2h_goal_diff=2, h2h_goals=4),
    GroupStanding(group="E", rank=3, team="Ecuador", points=4, goal_diff=0, goals_for=2, fifa_rank=23,
                  h2h_points=4, h2h_goal_diff=0, h2h_goals=2),
    GroupStanding(group="E", rank=4, team="Curaçao", points=1, goal_diff=-8, goals_for=1, fifa_rank=82,
                  h2h_points=1, h2h_goal_diff=-8, h2h_goals=1),

    # Group F
    GroupStanding(group="F", rank=1, team="Portugal", points=7, goal_diff=5, goals_for=6, fifa_rank=5,
                  h2h_points=7, h2h_goal_diff=5, h2h_goals=6),
    GroupStanding(group="F", rank=2, team="Colombia", points=5, goal_diff=2, goals_for=5, fifa_rank=13,
                  h2h_points=5, h2h_goal_diff=2, h2h_goals=5),
    GroupStanding(group="F", rank=3, team="Panama", points=3, goal_diff=-2, goals_for=3, fifa_rank=34,
                  h2h_points=3, h2h_goal_diff=-2, h2h_goals=3),
    GroupStanding(group="F", rank=4, team="New Zealand", points=1, goal_diff=-5, goals_for=1, fifa_rank=85,
                  h2h_points=1, h2h_goal_diff=-5, h2h_goals=1),

    # Group G
    GroupStanding(group="G", rank=1, team="Argentina", points=9, goal_diff=5, goals_for=7, fifa_rank=1,
                  h2h_points=9, h2h_goal_diff=5, h2h_goals=7),
    GroupStanding(group="G", rank=2, team="Netherlands", points=5, goal_diff=2, goals_for=5, fifa_rank=8,
                  h2h_points=5, h2h_goal_diff=2, h2h_goals=5),
    GroupStanding(group="G", rank=3, team="Austria", points=3, goal_diff=-1, goals_for=2, fifa_rank=24,
                  h2h_points=3, h2h_goal_diff=-1, h2h_goals=2),
    GroupStanding(group="G", rank=4, team="Iran", points=0, goal_diff=-6, goals_for=2, fifa_rank=20,
                  h2h_points=0, h2h_goal_diff=-6, h2h_goals=2),

    # Group H
    GroupStanding(group="H", rank=1, team="Uruguay", points=7, goal_diff=4, goals_for=8, fifa_rank=16,
                  h2h_points=7, h2h_goal_diff=4, h2h_goals=8),
    GroupStanding(group="H", rank=2, team="Belgium", points=6, goal_diff=3, goals_for=6, fifa_rank=9,
                  h2h_points=6, h2h_goal_diff=3, h2h_goals=6),
    GroupStanding(group="H", rank=3, team="Jordan", points=3, goal_diff=-2, goals_for=2, fifa_rank=63,
                  h2h_points=3, h2h_goal_diff=-2, h2h_goals=2),
    GroupStanding(group="H", rank=4, team="Saudi Arabia", points=1, goal_diff=-5, goals_for=2, fifa_rank=61,
                  h2h_points=1, h2h_goal_diff=-5, h2h_goals=2),

    # Group I
    GroupStanding(group="I", rank=1, team="France", points=9, goal_diff=7, goals_for=9, fifa_rank=3,
                  h2h_points=9, h2h_goal_diff=7, h2h_goals=9),
    GroupStanding(group="I", rank=2, team="Croatia", points=4, goal_diff=1, goals_for=4, fifa_rank=11,
                  h2h_points=4, h2h_goal_diff=1, h2h_goals=4),
    GroupStanding(group="I", rank=3, team="Egypt", points=3, goal_diff=-1, goals_for=3, fifa_rank=29,
                  h2h_points=3, h2h_goal_diff=-1, h2h_goals=3),
    GroupStanding(group="I", rank=4, team="Ghana", points=1, goal_diff=-7, goals_for=2, fifa_rank=73,
                  h2h_points=1, h2h_goal_diff=-7, h2h_goals=2),

    # Group J
    GroupStanding(group="J", rank=1, team="Spain", points=9, goal_diff=8, goals_for=10, fifa_rank=1,
                  h2h_points=9, h2h_goal_diff=8, h2h_goals=10),
    GroupStanding(group="J", rank=2, team="England", points=5, goal_diff=2, goals_for=5, fifa_rank=4,
                  h2h_points=5, h2h_goal_diff=2, h2h_goals=5),
    GroupStanding(group="J", rank=3, team="Algeria", points=4, goal_diff=0, goals_for=4, fifa_rank=28,
                  h2h_points=4, h2h_goal_diff=0, h2h_goals=4),
    GroupStanding(group="J", rank=4, team="Tunisia", points=0, goal_diff=-10, goals_for=1, fifa_rank=45,
                  h2h_points=0, h2h_goal_diff=-10, h2h_goals=1),

    # Group K
    GroupStanding(group="K", rank=1, team="Italy", points=7, goal_diff=4, goals_for=7, fifa_rank=12,
                  h2h_points=7, h2h_goal_diff=4, h2h_goals=7),
    GroupStanding(group="K", rank=2, team="Sweden", points=5, goal_diff=1, goals_for=4, fifa_rank=38,
                  h2h_points=5, h2h_goal_diff=1, h2h_goals=4),
    GroupStanding(group="K", rank=3, team="Nigeria", points=3, goal_diff=-1, goals_for=3, fifa_rank=28,
                  h2h_points=3, h2h_goal_diff=-1, h2h_goals=3),
    GroupStanding(group="K", rank=4, team="Uzbekistan", points=2, goal_diff=-4, goals_for=2, fifa_rank=50,
                  h2h_points=2, h2h_goal_diff=-4, h2h_goals=2),

    # Group L
    GroupStanding(group="L", rank=1, team="Japan", points=7, goal_diff=3, goals_for=6, fifa_rank=18,
                  h2h_points=7, h2h_goal_diff=3, h2h_goals=6),
    GroupStanding(group="L", rank=2, team="Senegal", points=5, goal_diff=1, goals_for=4, fifa_rank=15,
                  h2h_points=5, h2h_goal_diff=1, h2h_goals=4),
    GroupStanding(group="L", rank=3, team="Iraq", points=3, goal_diff=-1, goals_for=3, fifa_rank=57,
                  h2h_points=3, h2h_goal_diff=-1, h2h_goals=3),
    GroupStanding(group="L", rank=4, team="DR Congo", points=2, goal_diff=-3, goals_for=2, fifa_rank=46,
                  h2h_points=2, h2h_goal_diff=-3, h2h_goals=2),
]

ranker = ThirdPlaceRanker()
third_trace = ranker.rank(standings)
print(f"\n[ENGINE] Third-place ranking: {len(third_trace.qualifiers)} qualifiers, "
      f"{len(third_trace.eliminated)} eliminated")
for t in third_trace.qualifiers:
    print(f"  #{t.rank}: {t.team} ({t.group}) - {t.points}pts, GD={t.goal_diff}, "
          f"GF={t.goals_scored}, FIFA#{t.fifa_rank} -> QUALIFY")
for t in third_trace.eliminated:
    print(f"  #{t.rank}: {t.team} ({t.group}) - {t.points}pts, GD={t.goal_diff}, "
          f"GF={t.goals_scored}, FIFA#{t.fifa_rank} -> OUT")

# ── Block 3: ENGINE — R32 Builder ────────────────────────────────────────────
builder = R32Builder(rule)
r32_traces = builder.build(standings, third_trace)
print(f"\n[ENGINE] R32 generated: {len(r32_traces)} matches")
for t in r32_traces:
    marker = "[RUD]" if t.match_type == "runner_up_derby" else "[CvT]"
    print(f"  {marker} {t.match_id}: {t.home_team} vs {t.away_team} "
          f"({t.home_slot} vs {t.away_slot})")
    if t.match_type == "champion_vs_third":
        print(f"       QUAL_REASON: {t.qualification_reason}")

# ── Block 4: ENGINE — Knockout Simulator ─────────────────────────────────────
elo_map = {
    "Argentina": 1850, "Brazil": 1830, "France": 1820, "Spain": 1800,
    "Germany": 1790, "England": 1780, "Italy": 1770, "Netherlands": 1765,
    "Portugal": 1760, "Belgium": 1755, "Croatia": 1750, "Colombia": 1745,
    "Mexico": 1720, "Japan": 1710, "Switzerland": 1700, "Uruguay": 1725,
}
sim = KnockoutSimulator(elo_model=EloProbModel(elo_map))
result = sim.simulate(r32_traces)
print(f"\n[ENGINE] Knockout result:")
print(f"  CHAMPION:   {result.champion}")
print(f"  RUNNER-UP: {result.runner_up}")
print(f"  THIRD:      {result.third_place}")
print(f"  Final: {result.final['home_team']} vs {result.final['away_team']} "
      f"(H: {result.final['home_win_prob']:.0%})")

print("\nOK: IE-1 smoke test PASSED - all four blocks run end-to-end")
