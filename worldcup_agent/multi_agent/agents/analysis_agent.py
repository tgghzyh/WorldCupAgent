"""Analysis Agent — analyzes team strengths and matchup dynamics.

This agent implements the ReAct pattern for tactical analysis:
  1. OBSERVE: Gather team data and recent results
  2. THINK: Reason about key factors and team form
  3. ACT: Generate analysis report
  4. EVALUATE: Check analysis completeness
  5. REVISE: Refine analysis if needed
"""
from __future__ import annotations

from typing import Any

from worldcup_agent.multi_agent import BaseAgent, WorldState


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent — tactical analyst for match predictions.

    ReAct Loop:
      OBSERVE: Gather team data, form, injuries
      THINK:   Identify key factors and dynamics
      ACT:     Generate comprehensive analysis
      EVALUATE: Check completeness and consistency
      REVISE:  Refine if analysis is incomplete
    """

    def __init__(self):
        super().__init__(
            name="analysis_agent",
            description="Analyzes team strengths and matchup dynamics",
            max_iterations=2,
        )
        self._analysis_cache: dict[str, dict] = {}

    @property
    def system_prompt(self) -> str:
        return """You are the Analysis Agent for WC2026 predictions.

Your responsibilities:
  1. Analyze team strengths and weaknesses
  2. Identify key factors for each matchup
  3. Assess team form and momentum
  4. Evaluate tactical matchups

You do NOT make predictions — you provide the analytical foundation
that other agents (Simulation, Prediction) will use.

Analysis should include:
  - Team Elo ratings and their implications
  - Recent form (wins/losses in last 5-10 matches)
  - Head-to-head history
  - Home/away performance patterns
  - Key player availability (injuries, suspensions)
  - Tactical style matchups (attacking vs defensive)
"""

    def observe(self, state: WorldState) -> dict:
        """OBSERVE: Gather data for analysis."""
        observation = {
            "teams_available": len(state.teams),
            "recent_results": len(state.match_results),
            "tournament_stage": state.tournament_stage,
            "teams": list(state.teams.keys())[:10],  # Sample
        }

        # Analyze team states
        team_states = []
        for team_name, team_data in list(state.teams.items())[:8]:
            if isinstance(team_data, dict):
                team_states.append({
                    "name": team_name,
                    "elo": team_data.get("elo", 1500),
                    "form": team_data.get("form_score", 0.5),
                    "group": team_data.get("group", ""),
                })

        observation["team_states"] = team_states

        # Recent match results for form analysis
        recent_matches = []
        for result in state.match_results[-10:]:
            recent_matches.append({
                "home": result.get("home_team", ""),
                "away": result.get("away_team", ""),
                "score": f"{result.get('home_score', 0)}-{result.get('away_score', 0)}",
            })

        observation["recent_matches"] = recent_matches

        return observation

    def think(self, observation: dict, state: WorldState) -> str:
        """THINK: Reason about key factors."""
        teams_count = observation.get("teams_available", 0)

        if teams_count < 48:
            return f"ANALYSIS_PARTIAL: Only {teams_count} teams available. " \
                   f"Will analyze available teams and note gaps."

        if observation.get("recent_results", 0) > 0:
            return "ANALYSIS_WITH_RESULTS: Have real match results. " \
                   "Will factor in actual performance into analysis."

        return "ANALYSIS_BASELINE: No tournament results yet. " \
               "Will base analysis on Elo ratings and historical form only."

    def act(self, thought: str, state: WorldState) -> tuple[dict, str]:
        """ACT: Generate comprehensive team analysis."""
        analysis = {
            "team_analyses": {},
            "key_factors": [],
            "matchup_insights": [],
        }

        # Analyze each team
        for team_name, team_data in state.teams.items():
            if not isinstance(team_data, dict):
                continue

            elo = team_data.get("elo", 1500)
            form_score = team_data.get("form_score", 0.5)
            rank = team_data.get("rank", 120)

            # Determine tier based on Elo
            if elo >= 2000:
                tier = "elite"
                tier_desc = "World-class team with exceptional quality"
            elif elo >= 1800:
                tier = "strong"
                tier_desc = "Strong team with good infrastructure"
            elif elo >= 1600:
                tier = "competitive"
                tier_desc = "Competitive team, capable of upsets"
            else:
                tier = "developing"
                tier_desc = "Developing team with limited resources"

            analysis["team_analyses"][team_name] = {
                "elo": elo,
                "rank": rank,
                "form_score": form_score,
                "tier": tier,
                "tier_description": tier_desc,
                "strengths": self._identify_strengths(team_data),
                "weaknesses": self._identify_weaknesses(team_data),
                "form_trend": self._calculate_form_trend(team_data),
            }

        # Identify cross-team key factors
        analysis["key_factors"] = self._identify_key_factors(state.teams)

        # Generate matchup insights for potential games
        matchups = self._generate_matchup_insights(state.teams)
        analysis["matchup_insights"] = matchups

        observation = f"Analyzed {len(analysis['team_analyses'])} teams. " \
                      f"Identified {len(analysis['key_factors'])} key factors. " \
                      f"Generated {len(matchups)} matchup insights."

        return analysis, observation

    def evaluate(self, result: dict, state: WorldState) -> bool:
        """EVALUATE: Check analysis quality."""
        if not result.get("team_analyses"):
            return False

        # Should have analyzed most teams
        if len(result["team_analyses"]) < len(state.teams) * 0.8:
            return False

        return True

    def revise(self, result: Any, error: str, state: WorldState) -> str:
        """REVISE: Expand analysis coverage."""
        return "Expanding analysis to cover all available teams with basic metrics."

    # ── Helper Methods ──────────────────────────────────────────────────────

    def _identify_strengths(self, team_data: dict) -> list[str]:
        """Identify team strengths."""
        strengths = []
        elo = team_data.get("elo", 1500)
        form = team_data.get("form_score", 0.5)

        if elo >= 1900:
            strengths.append("Exceptional squad depth")
        if form >= 0.7:
            strengths.append("Excellent recent form")
        if team_data.get("rank", 120) <= 20:
            strengths.append("Elite FIFA ranking")
        if team_data.get("elo", 1500) > 1700:
            strengths.append("Strong Elo rating indicates consistency")

        return strengths or ["Balanced team profile"]

    def _identify_weaknesses(self, team_data: dict) -> list[str]:
        """Identify team weaknesses."""
        weaknesses = []
        elo = team_data.get("elo", 1500)
        form = team_data.get("form_score", 0.5)

        if elo < 1600:
            weaknesses.append("Limited international experience")
        if form < 0.4:
            weaknesses.append("Poor recent form")
        if team_data.get("injury_impact", 0) < -0.1:
            weaknesses.append("Significant injury concerns")

        return weaknesses or ["Standard team with no major weaknesses identified"]

    def _calculate_form_trend(self, team_data: dict) -> str:
        """Calculate form trend."""
        form = team_data.get("form_score", 0.5)

        if form >= 0.7:
            return "rising"  # In form
        elif form <= 0.3:
            return "falling"  # Out of form
        else:
            return "stable"

    def _identify_key_factors(self, teams: dict) -> list[dict]:
        """Identify cross-team key factors."""
        factors = []

        # Find elite teams
        elite_teams = [
            name for name, data in teams.items()
            if isinstance(data, dict) and data.get("elo", 1500) >= 2000
        ]

        if elite_teams:
            factors.append({
                "type": "elite_teams",
                "description": f"{len(elite_teams)} teams with Elo >= 2000 (elite tier)",
                "teams": elite_teams,
                "impact": "high",
            })

        # Find potential dark horses (good Elo but not top tier)
        dark_horses = [
            name for name, data in teams.items()
            if isinstance(data, dict)
            and 1700 <= data.get("elo", 1500) < 2000
            and data.get("form_score", 0.5) >= 0.6
        ]

        if dark_horses:
            factors.append({
                "type": "dark_horses",
                "description": f"{len(dark_horses)} teams with strong form but not elite Elo",
                "teams": dark_horses,
                "impact": "medium",
            })

        return factors

    def _generate_matchup_insights(self, teams: dict) -> list[dict]:
        """Generate insights for notable matchups."""
        insights = []

        # Sample matchups between groups
        group_teams = {}
        for name, data in teams.items():
            if isinstance(data, dict):
                group = data.get("group", "")
                if group:
                    if group not in group_teams:
                        group_teams[group] = []
                    group_teams[group].append((name, data.get("elo", 1500)))

        # Generate intra-group matchup insights
        for group, team_list in list(group_teams.items())[:3]:
            if len(team_list) >= 2:
                # Top two in group
                sorted_teams = sorted(team_list, key=lambda x: x[1], reverse=True)
                if len(sorted_teams) >= 2:
                    team1, elo1 = sorted_teams[0]
                    team2, elo2 = sorted_teams[1]
                    elo_diff = elo1 - elo2

                    insights.append({
                        "type": "group_favorites",
                        "group": group,
                        "matchup": f"{team1} vs {team2}",
                        "analysis": f"{team1} (Elo: {elo1}) is {elo_diff:.0f} points higher than {team2} (Elo: {elo2})",
                        "prediction_factors": [
                            f"{team1} has significant Elo advantage",
                            "Group stage dynamics favor consistent performers",
                        ],
                    })

        return insights
