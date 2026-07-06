"""WC2026 Prediction Agent — Agentic Orchestrator.

Unlike a sequential pipeline, this agent:
  1. PLANS   — decides what predictions to make today
  2. SEARCHES — checks if new data is available (Elo refresh, injury news)
  3. TOOLS    — calls the right data source based on freshness
  4. REASONS  — builds feature vectors and runs explainability
  5. PREDICTS — generates probabilities with full attribution
  6. VISUALISES — produces the daily intelligence briefing

Plus the CLOSED-LOOP extension:
  7. OBSERVE  — watches for real match results
  8. UPDATE    — updates world state based on results
  9. LOOP     — re-predicts remaining matches with updated state

Usage:
  python -m worldcup_agent.prediction.agent
  python -m worldcup_agent.prediction.agent --force-refresh  # bypass TTL
  python -m worldcup_agent.prediction.agent --compare        # diff vs previous snapshot

Closed-loop mode (for real tournament):
  python -m worldcup_agent.prediction.agent --loop --interval 3600
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

import pandas as pd

from worldcup_agent.elo_ratings import run as refresh_elo
from worldcup_agent.prediction.prediction_schema import (
    FactorAttribution,
    MatchPrediction,
    OutcomeProbability,
    PredictionSnapshot,
    SNAPSHOT_DIR,
    get_knowledge_version,
    get_pipeline_version,
    save_snapshot,
)
from worldcup_agent.prediction.elo_system import ELOSystem
from worldcup_agent.prediction.world_state import (
    WorldState,
    MatchResult,
    load_world_state,
    save_world_state,
)
from worldcup_agent.prediction.observer import (
    TournamentObserver,
    ObservationSet,
)
from worldcup_agent.prediction.llm_engine import (
    LLMEngine,
    create_llm_engine,
)

# ── Agent State ─────────────────────────────────────────────────────────────────

@dataclass
class AgentState:
    """Mutable state carried through the agent loop."""
    step: Literal[
        "idle", "plan", "search", "tools", "reason",
        "predict", "observe", "update", "done"
    ]
    messages: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    data_fresh: bool = False
    prediction_version: str = ""
    knowledge_version: str = ""
    snapshot: PredictionSnapshot | None = None
    error: str | None = None

    # Closed-loop state
    world_state: WorldState | None = None
    observations: ObservationSet | None = None
    update_reasons: list[str] = field(default_factory=list)
    loop_iteration: int = 0

    # LLM reasoning
    llm_enabled: bool = True
    llm_reasoning: dict = field(default_factory=dict)  # match_id -> reasoning text
    llm_latency_ms: float = 0.0


@dataclass
class ToolResult:
    """Standard return type from any agent tool."""
    tool: str
    ok: bool
    data: dict | None = None
    message: str = ""
    warnings: list[str] = field(default_factory=list)


# ── Tool Registry ───────────────────────────────────────────────────────────────

class ToolRegistry:
    """Simulates an agent's available tools. In production, each maps to a real API/tool."""

    def __init__(self, force_refresh: bool = False):
        self.force_refresh = force_refresh
        self._elo_system = ELOSystem()

    def refresh_elo_ratings(self) -> ToolResult:
        """Fetch latest Elo ratings from eloratings.net (respects TTL)."""
        try:
            result = refresh_elo(force_refresh=self.force_refresh)
            return ToolResult(
                tool="refresh_elo_ratings",
                ok=result.get("ok", False),
                data=result,
                message=f"Elo: {result.get('teams_matched', '?')} teams matched",
            )
        except Exception as e:
            return ToolResult(tool="refresh_elo_ratings", ok=False, message=str(e))

    def get_team_features(self) -> ToolResult:
        """Load current team feature vector (Elo + rank + history)."""
        try:
            root = Path(__file__).resolve().parents[2]   # project root
            enriched_path = root / "worldcup_agent" / "data_layer" / "cleaned" / "teams_2026_enriched.json"
            data = json.loads(enriched_path.read_text(encoding="utf-8"))
            teams = data.get("teams", [])
            return ToolResult(
                tool="get_team_features",
                ok=True,
                data={"teams": teams, "count": len(teams)},
            )
        except Exception as e:
            return ToolResult(tool="get_team_features", ok=False, message=str(e))

    def get_historical_matches(self) -> ToolResult:
        """Load WC historical match outcomes for model training."""
        try:
            root = Path(__file__).resolve().parents[2]
            df = pd.read_csv(
                root / "worldcup_agent" / "data_layer" / "cleaned" / "world_cup_finals_only.csv"
            )
            return ToolResult(
                tool="get_historical_matches",
                ok=True,
                data={"rows": len(df), "years": sorted(df["date"].str[:4].unique())},
            )
        except Exception as e:
            return ToolResult(tool="get_historical_matches", ok=False, message=str(e))

    def check_injury_news(self) -> ToolResult:
        """Placeholder for real injury/news API integration.

        In production this would call a live sports news API.
        Returns empty impact list with a warning that integration is pending.
        """
        return ToolResult(
            tool="check_injury_news",
            ok=True,
            data={"impacts": [], "note": "integration pending"},
            warnings=["Injury/news API not yet integrated"],
        )


# ── Explainability Engine ──────────────────────────────────────────────────────

class ExplainabilityEngine:
    """Post-hoc explanation of why a probability is what it is.

    Uses feature contribution analysis to decompose the probability
    into ranked factors with plain-English evidence.
    """

    # Named factor definitions — maps model features to human-readable explanations
    FACTOR_DEFINITIONS = {
        "elo_diff": {
            "name": "ELO Rating Advantage",
            "weight": 0.42,
            "direction_up_means": "home team has higher Elo",
            "format_evidence": lambda h, a, v: f"Home Elo {h} vs Away Elo {a} (diff {v:+.0f})",
            "confidence_fn": lambda v: "high" if abs(v) > 50 else "medium" if abs(v) > 20 else "low",
        },
        "rank_diff": {
            "name": "FIFA World Ranking Advantage",
            "weight": 0.26,
            "direction_up_means": "home team has better (lower) FIFA rank",
            "format_evidence": lambda h, a, v: f"Home rank {h} vs Away rank {a} (lower is better)",
            "confidence_fn": lambda v: "high" if abs(v) > 0.1 else "medium",
        },
        "recent_form": {
            "name": "Recent Match Form",
            "weight": 0.18,
            "direction_up_means": "home team has more wins in recent A-matches",
            "format_evidence": lambda h, a, v: f"Home form score {h:.1f} vs Away {a:.1f}",
            "confidence_fn": lambda v: "high" if abs(v) > 0.15 else "medium",
        },
        "xg_advantage": {
            "name": "Historical xG Efficiency",
            "weight": 0.14,
            "direction_up_means": "home team converts chances better historically",
            "format_evidence": lambda h, a, v: f"Home xG/shot {h:.2f} vs Away {a:.2f}",
            "confidence_fn": lambda v: "medium" if abs(v) > 0.02 else "low",
        },
    }

    def explain(
        self,
        home_team: str,
        away_team: str,
        home_features: dict,
        away_features: dict,
        outcome: OutcomeProbability,
        model_contribution: dict[str, float],  # feature → raw contribution
    ) -> list[FactorAttribution]:
        """Build ranked factor attributions for one match prediction."""
        factors = []

        # ELO diff
        h_elo = home_features.get("elo_rating_live", 1500)
        a_elo = away_features.get("elo_rating_live", 1500)
        elo_diff = h_elo - a_elo
        elo_contrib = abs(model_contribution.get("elo_diff", 0))
        factors.append(FactorAttribution(
            name="ELO Rating Advantage",
            key="elo_diff",
            value=elo_diff,
            contribution_pct=self.FACTOR_DEFINITIONS["elo_diff"]["weight"],
            direction="up" if elo_diff > 0 else "down",
            evidence=f"Home Elo {h_elo} vs Away Elo {a_elo} (diff {elo_diff:+.0f})",
            confidence=self.FACTOR_DEFINITIONS["elo_diff"]["confidence_fn"](elo_diff),
        ))

        # Rank diff
        h_rank = home_features.get("world_rank_live", 120)
        a_rank = away_features.get("world_rank_live", 120)
        rank_diff = a_rank - h_rank  # positive = home has better (lower) rank
        factors.append(FactorAttribution(
            name="FIFA World Ranking Advantage",
            key="rank_diff",
            value=rank_diff,
            contribution_pct=self.FACTOR_DEFINITIONS["rank_diff"]["weight"],
            direction="up" if rank_diff > 0 else "down",
            evidence=f"Home rank #{h_rank} vs Away rank #{a_rank}",
            confidence="high" if abs(rank_diff) > 10 else "medium" if abs(rank_diff) > 3 else "low",
        ))

        # Recent form (if available)
        h_form = home_features.get("recent_form_score")
        a_form = away_features.get("recent_form_score")
        if h_form is not None and a_form is not None:
            form_diff = h_form - a_form
            factors.append(FactorAttribution(
                name="Recent Match Form",
                key="recent_form",
                value=form_diff,
                contribution_pct=self.FACTOR_DEFINITIONS["recent_form"]["weight"],
                direction="up" if form_diff > 0 else "down",
                evidence=f"Home: {h_form:.1f} pts (last 10 A-matches) vs Away: {a_form:.1f}",
                confidence="medium",
            ))

        # Sort by contribution weight (descending)
        factors.sort(key=lambda f: f.contribution_pct, reverse=True)
        return factors


# ── Agent Loop ─────────────────────────────────────────────────────────────────

class WC2026Agent:
    """
    The main agent orchestrator.

    This is a CLOSED-LOOP Agent that:
    1. Maintains WorldState (memory of tournament progress)
    2. Observes real match results (from data sources)
    3. Updates internal state based on observations
    4. Re-predicts remaining matches with updated information
    5. Loops continuously during the tournament

    The loop: Observe → Reason → Act → Observe → ...
    """

    def __init__(self, force_refresh: bool = False, verbose: bool = True, use_llm: bool = True):
        self.tools = ToolRegistry(force_refresh=force_refresh)
        self.explainer = ExplainabilityEngine()
        self.observer = TournamentObserver()
        self.verbose = verbose
        self.state = AgentState(step="idle", llm_enabled=use_llm)
        self._log: list[str] = []

        # Initialize LLM engine
        self.llm: LLMEngine | None = None
        if use_llm:
            try:
                self.llm = create_llm_engine()
                self._log_msg("LLM: Enabled (using qwen-plus)")
            except Exception as e:
                self._log_msg(f"LLM: Failed to initialize - {e}")
                self.state.llm_enabled = False

        # Load or initialize WorldState
        self.world_state = load_world_state()

    def _log_msg(self, msg: str) -> None:
        self._log.append(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}")
        if self.verbose:
            print(f"  > {msg}")

    # ══════════════════════════════════════════════════════════════════════
    # MAIN ENTRY POINTS
    # ══════════════════════════════════════════════════════════════════════

    def run(self) -> PredictionSnapshot:
        """
        Execute ONE iteration of the agent loop.

        Returns a PredictionSnapshot with updated predictions.
        """
        self.state.loop_iteration += 1
        self._log_msg(f"═══ Agent Loop Iteration #{self.state.loop_iteration} ═══")

        # Step 1: Observe - check for new data
        self.state.step = "observe"
        self._observe()

        # Step 2: Plan - decide what to do
        self.state.step = "plan"
        self._plan()

        # Step 3: Search - check data freshness
        self.state.step = "search"
        self._search()

        # Step 4: Tools - execute data fetching
        self.state.step = "tools"
        tool_results = self._execute_tools()

        # Step 5: Reason - interpret results
        self.state.step = "reason"
        self._reason(tool_results)

        # Step 6: Predict - generate predictions
        self.state.step = "predict"
        snapshot = self._predict(tool_results)

        # Step 7: Update - save world state
        self.state.step = "update"
        self._update_world_state()

        self.state.step = "done"
        self.state.snapshot = snapshot
        return snapshot

    def run_loop(self, interval: int = 3600, max_iterations: int | None = None) -> None:
        """
        Run the agent in a CONTINUOUS LOOP (closed-loop mode).

        This is the production mode during the actual tournament.

        Args:
            interval: Seconds between each iteration (default: 3600 = 1 hour)
            max_iterations: Optional cap on iterations (for testing)

        The loop:
        ┌─────────────────────────────────────────────────────┐
        │  while True:                                       │
        │      observe()     ← Get real match results        │
        │      if world_changed:                             │
        │          update_world_state()                      │
        │          re_predict()   ← Update predictions       │
        │      save_snapshot()                               │
        │      wait(interval)                                │
        └─────────────────────────────────────────────────────┘
        """
        self._log_msg("═══ ENTERING CLOSED-LOOP MODE ═══")
        self._log_msg(f"Loop interval: {interval}s ({interval/3600:.1f}h)")

        iteration = 0
        while True:
            iteration += 1
            if max_iterations and iteration > max_iterations:
                self._log_msg(f"Reached max iterations ({max_iterations}). Stopping.")
                break

            self._log_msg(f"\n{'='*50}")
            self._log_msg(f"LOOP ITERATION #{iteration} — {datetime.now():%Y-%m-%d %H:%M:%S}")
            self._log_msg(f"{'='*50}")

            try:
                # Run one iteration
                self.run()

                # Check if tournament is over
                if self.world_state and self._is_tournament_over():
                    self._log_msg("Tournament complete. Exiting loop.")
                    break

            except KeyboardInterrupt:
                self._log_msg("Received interrupt signal. Saving state and exiting.")
                break
            except Exception as e:
                self._log_msg(f"ERROR in iteration: {e}")
                # Continue loop even on error

            self._log_msg(f"Sleeping for {interval}s until next iteration...")
            time.sleep(interval)

    # ══════════════════════════════════════════════════════════════════════
    # CLOSED-LOOP: OBSERVE
    # ══════════════════════════════════════════════════════════════════════

    def _observe(self) -> None:
        """
        OBSERVE step: Gather new information from the world.

        This is what makes this an Agent (not a pipeline).
        The agent watches for:
        - New match results
        - Team news (injuries, suspensions)
        - Schedule changes
        """
        self._log_msg("OBSERVE: Checking for new tournament data...")

        observations = self.observer.observe(self.world_state)
        self.state.observations = observations

        if observations.has_new_data:
            self._log_msg(f"  Found {len(observations.observations)} new observations:")
            for obs in observations.observations:
                self._log_msg(f"    [{obs.obs_type}] {obs.data.get('summary', '')}")

            # Log high-priority observations
            high_priority = observations.high_priority
            if high_priority:
                self._log_msg(f"  HIGH PRIORITY ({len(high_priority)}):")
                for obs in high_priority:
                    self._log_msg(f"    ⚡ {obs}")
        else:
            self._log_msg("  No new data. Tournament state unchanged.")

    # ══════════════════════════════════════════════════════════════════════
    # CLOSED-LOOP: UPDATE WORLD STATE
    # ══════════════════════════════════════════════════════════════════════

    def _update_world_state(self) -> None:
        """
        UPDATE step: Incorporate observations into WorldState.

        This is the KEY difference from a batch pipeline.
        The agent:
        1. Records new match results
        2. Updates team strength estimates
        3. Adjusts predictions for remaining matches
        4. Persists state for the next iteration
        """
        if not self.state.observations or not self.state.observations.has_new_data:
            self._log_msg("UPDATE: No changes to world state.")
            return

        self._log_msg("UPDATE: Processing observations and updating world state...")

        # Initialize world state if needed
        if self.world_state is None:
            self.world_state = WorldState()
            self._initialize_world_state()

        update_reasons: list[str] = []

        # Process each observation
        for obs in self.state.observations.observations:
            if obs.obs_type == "match_result":
                reason = self._process_match_result(obs)
                if reason:
                    update_reasons.append(reason)

            elif obs.obs_type == "team_news":
                reason = self._process_team_news(obs)
                if reason:
                    update_reasons.append(reason)

            elif obs.obs_type == "bracket_update":
                update_reasons.append("Bracket structure updated based on new results")

        # Save updated state
        self.state.update_reasons = update_reasons
        save_world_state(self.world_state)

        if update_reasons:
            self._log_msg(f"  World state updated. Reasons:")
            for reason in update_reasons:
                self._log_msg(f"    → {reason}")
        else:
            self._log_msg("  World state unchanged (no actionable observations).")

    def _process_match_result(self, obs: Observation) -> str | None:
        """Process a match result observation and update world state."""
        data = obs.data

        # Check if we already have this result
        existing_ids = {r.match_id for r in self.world_state.results}
        if data.get("match_id") in existing_ids:
            return None

        # Create MatchResult
        result = MatchResult(
            match_id=data["match_id"],
            home_team=data["home_team"],
            away_team=data["away_team"],
            home_score=data.get("home_score", 0),
            away_score=data.get("away_score", 0),
            stage=data.get("stage", "group"),
            kickoff=data.get("kickoff", datetime.now(timezone.utc).isoformat()),
        )

        # Add to world state
        self.world_state.add_result(result)

        # Determine reason for prediction update
        reason = f"Match result: {result.home_team} {result.home_score}-{result.away_score} {result.away_team}"

        if result.winner:
            reason += f" -> {result.winner} wins"
        else:
            reason += " -> Draw"

        # LLM Analysis (NEW)
        if self.llm and self.state.llm_enabled:
            try:
                llm_result = self.llm.analyze_match_result(
                    home_team=result.home_team,
                    away_team=result.away_team,
                    home_score=result.home_score,
                    away_score=result.away_score,
                    world_state_context=self._get_world_state_summary(),
                )
                if llm_result.success:
                    self._log_msg(f"  LLM analysis: {llm_result.content[:100]}...")
                    self.state.llm_latency_ms += llm_result.latency_ms
            except Exception as e:
                self._log_msg(f"  LLM analysis failed: {e}")

        return reason

    def _get_world_state_summary(self) -> str:
        """Get a summary of current world state for LLM context."""
        if not self.world_state:
            return "No tournament data available."

        results_count = len(self.world_state.results)
        teams_count = len(self.world_state.teams)

        top_teams = []
        for name, team in list(self.world_state.teams.items())[:3]:
            if team.played > 0:
                top_teams.append(f"{name} ({team.won}W-{team.drawn}D-{team.lost}L)")

        summary = f"Tournament: {results_count} matches completed, {teams_count} teams tracked. "
        if top_teams:
            summary += f"Top performers: {', '.join(top_teams)}."
        else:
            summary += "Tournament just starting."

        return summary

    def _process_team_news(self, obs: Observation) -> str | None:
        """Process team news (injury, etc.) and update team state."""
        data = obs.data
        team_name = data.get("team")

        if not team_name or team_name not in self.world_state.teams:
            return None

        team = self.world_state.teams[team_name]
        severity = data.get("severity", 0.0)

        # Apply injury impact
        team.injury_impact = max(team.injury_impact, -severity)

        news_type = data.get("type", "other")
        return f"{team_name}: {news_type} impact (severity={severity:.2f})"

    def _initialize_world_state(self) -> None:
        """Initialize WorldState with team data from tools."""
        # Load team data
        try:
            root = Path(__file__).resolve().parents[2]
            enriched_path = root / "worldcup_agent" / "data_layer" / "cleaned" / "teams_2026_enriched.json"
            data = json.loads(enriched_path.read_text(encoding="utf-8"))

            for team_data in data.get("teams", []):
                name = team_data.get("team_2026_name", "")
                elo = team_data.get("elo_rating_live", 1500)
                group = team_data.get("group", "")

                self.world_state.add_team(name, elo=elo, group=group)

            self._log_msg(f"  WorldState initialized with {len(self.world_state.teams)} teams")
        except Exception as e:
            self._log_msg(f"  WARNING: Could not initialize WorldState: {e}")

    def _is_tournament_over(self) -> bool:
        """Check if the tournament is complete."""
        if not self.world_state:
            return False

        # Check if we have final results
        final_results = [r for r in self.world_state.results if r.stage == "final"]
        return len(final_results) > 0

    # ══════════════════════════════════════════════════════════════════════
    # ORIGINAL STEPS (Plan, Search, Tools, Reason, Predict)
    # ══════════════════════════════════════════════════════════════════════

    # ── Step 1: Plan ──────────────────────────────────────────────────────────

    def _plan(self) -> None:
        """Decide what to do today based on tournament state."""
        self._log_msg("PLANNING: assessing today's objectives")

        # Dynamic planning based on tournament state
        if self.world_state:
            stage = self.world_state.current_stage
            results_count = len(self.world_state.results)
            pending = len(self.world_state.pending_matches)

            plan_msg = (
                f"Current stage: {stage}. "
                f"Results recorded: {results_count}. "
                f"Pending predictions: {pending}. "
            )

            # Check if we need to update bracket
            if self.world_state.should_repredict():
                plan_msg += "Will update predictions based on new data."
            else:
                plan_msg += "No significant changes detected."
        else:
            plan_msg = "Initial prediction run. Generating baseline predictions."

        self.state.messages.append(f"Goal: Generate updated prediction snapshot. {plan_msg}")
        self._log_msg(f"Plan: {plan_msg}")

    # ── Step 2: Search ───────────────────────────────────────────────────────

    def _search(self) -> None:
        """Check what data is fresh and what needs updating."""
        self._log_msg("SEARCHING: checking knowledge base freshness")

        search_notes = []
        if self.state.observations and self.state.observations.has_new_data:
            search_notes.append("New observations available from tournament")
        if self.world_state and self.world_state.results:
            search_notes.append(f"{len(self.world_state.results)} real results in state")

        self.state.messages.append(
            f"Checking Elo freshness (TTL=7d). "
            f"Checking if team features need re-fetch. "
            f"{' '.join(search_notes) if search_notes else ''}"
        )

    # ── Step 3: Execute Tools ────────────────────────────────────────────────

    def _execute_tools(self) -> dict[str, ToolResult]:
        """Call all relevant tools and collect results."""
        self._log_msg("TOOLS: calling data sources")
        results = {}

        elo = self.tools.refresh_elo_ratings()
        results["elo"] = elo
        self.state.tools_used.append("refresh_elo_ratings")
        if elo.ok:
            self._log_msg(f"  Elo: {elo.message}")
        else:
            self._log_msg(f"  Elo FAILED: {elo.message}")

        features = self.tools.get_team_features()
        results["features"] = features
        self.state.tools_used.append("get_team_features")
        if features.ok:
            self._log_msg(f"  Team features: {features.data['count']} teams loaded")

        matches = self.tools.get_historical_matches()
        results["matches"] = matches
        self.state.tools_used.append("get_historical_matches")
        if matches.ok:
            self._log_msg(f"  Historical matches: {matches.data['rows']} rows")

        injuries = self.tools.check_injury_news()
        results["injuries"] = injuries
        self.state.tools_used.append("check_injury_news")
        if injuries.warnings:
            for w in injuries.warnings:
                self._log_msg(f"  WARNING: {w}")

        return results

    # ── Step 4: Reason ───────────────────────────────────────────────────────

    def _reason(self, tool_results: dict[str, ToolResult]) -> None:
        """Interpret tool outputs and decide prediction strategy."""
        self._log_msg("REASONING: building feature vectors and prediction strategy")
        if not tool_results.get("elo", ToolResult("", False)).ok:
            self.state.error = "Elo refresh failed; predictions will use cached data"
            self._log_msg(f"  WARNING: {self.state.error}")

    # ── Step 5: Predict ───────────────────────────────────────────────────────

    def _predict(self, tool_results: dict[str, ToolResult]) -> PredictionSnapshot:
        """
        Generate all match predictions with explainability.

        This method now uses WorldState for dynamic predictions:
        - Team strength multipliers from actual performance
        - Injury impacts from news
        - Updated bracket from real results
        """
        self._log_msg("PREDICTING: running model + explainability")

        teams_data = tool_results.get("features", ToolResult("", False)).data or {}
        team_list: list[dict] = teams_data.get("teams", [])

        # Build Elo map with WorldState adjustments
        elo_map: dict[str, float] = {}
        for t in team_list:
            name = t.get("team_2026_name", "")
            base_elo = t.get("elo_rating_live", 1500)

            # Apply WorldState adjustments if available
            if self.world_state and name in self.world_state.teams:
                team_state = self.world_state.teams[name]
                # Use effective Elo (includes form multiplier and injury impact)
                elo_map[name] = team_state.effective_elo()
            else:
                elo_map[name] = base_elo

        rank_map = {
            t.get("team_2026_name", ""): t.get("world_rank_live", 120)
            for t in team_list
        }

        elo_system = ELOSystem()

        match_predictions: list[MatchPrediction] = []
        teams_2026 = {t["team_2026_name"]: t["group"] for t in team_list}

        # Determine which matches to predict based on tournament state
        for home, home_grp in teams_2026.items():
            for away, away_grp in teams_2026.items():
                if home >= away or home_grp != away_grp:
                    continue  # same-group only for now

                # Check if this match already has a result
                if self._match_has_result(home, away):
                    self._log_msg(f"  SKIP {home} vs {away} — already played")
                    continue

                # Get dynamic Elo
                h_elo = elo_map.get(home, 1500)
                a_elo = elo_map.get(away, 1500)
                h_rank = rank_map.get(home, 120)
                a_rank = rank_map.get(away, 120)

                # Get WorldState info if available
                home_state = self.world_state.teams.get(home) if self.world_state else None
                away_state = self.world_state.teams.get(away) if self.world_state else None

                # Simulate prediction using Elo
                proba = elo_system.expected_score(h_elo, a_elo)
                outcome = OutcomeProbability(
                    home_win=round(proba[0], 4),
                    draw=round(proba[1], 4),
                    away_win=round(proba[2], 4),
                )

                # Apply WorldState adjustments to probability
                if home_state or away_state:
                    adj = self._compute_probability_adjustment(home, away, outcome)
                    outcome.home_win = round(max(0, outcome.home_win + adj), 4)
                    outcome.draw = round(max(0, outcome.draw), 4)
                    outcome.away_win = round(max(0, outcome.away_win - adj), 4)

                    # Renormalize
                    total = outcome.home_win + outcome.draw + outcome.away_win
                    if total > 0:
                        outcome.home_win = round(outcome.home_win / total, 4)
                        outcome.draw = round(outcome.draw / total, 4)
                        outcome.away_win = round(outcome.away_win / total, 4)

                # Explainability
                factors = self.explainer.explain(
                    home, away,
                    {"elo_rating_live": h_elo, "world_rank_live": h_rank},
                    {"elo_rating_live": a_elo, "world_rank_live": a_rank},
                    outcome,
                    model_contribution={"elo_diff": abs(h_elo - a_elo)},
                )

                # Add WorldState factors if relevant
                if home_state and abs(home_state.strength_multiplier - 1.0) > 0.01:
                    factors.append(FactorAttribution(
                        name="Recent Form Adjustment",
                        key="form_multiplier",
                        value=home_state.strength_multiplier - 1.0,
                        contribution_pct=0.08,
                        direction="up" if home_state.strength_multiplier > 1.0 else "down",
                        evidence=f"Based on recent {home_state.won}W/{home_state.drawn}D/{home_state.lost}L performance",
                        confidence="medium",
                    ))
                if away_state and away_state.injury_impact < 0:
                    factors.append(FactorAttribution(
                        name="Injury Impact",
                        key="injury",
                        value=away_state.injury_impact,
                        contribution_pct=0.05,
                        direction="down",
                        evidence=f"{away_state.name} affected by injuries (impact: {away_state.injury_impact:.2f})",
                        confidence="low",
                    ))

                # Sort by contribution weight (descending)
                factors.sort(key=lambda f: f.contribution_pct, reverse=True)

                # Predicted winner (most likely outcome, skip draw for "winner")
                if outcome.home_win > max(outcome.draw, outcome.away_win):
                    pred_winner = home
                elif outcome.away_win > max(outcome.home_win, outcome.draw):
                    pred_winner = away
                else:
                    pred_winner = None  # draw most likely

                match_predictions.append(MatchPrediction(
                    match_id=f"wc2026_{home[:3].upper()}_{away[:3].upper()}",
                    home_team=home,
                    away_team=away,
                    kickoff="2026-07-14T00:00:00Z",  # placeholder
                    outcome=outcome,
                    predicted_winner=pred_winner if pred_winner != "draw" else None,
                    factors=factors,
                    model_used="elo_system_v1_with_world_state",
                    training_set_size=448,
                ))

        # ── LLM Reasoning (NEW) ──────────────────────────────────────────────
        if self.llm and self.state.llm_enabled:
            self._log_msg("LLM: Generating reasoning for predictions...")
            llm_start = datetime.now(timezone.utc)

            # Generate reasoning for key matches
            for pred in match_predictions[:5]:  # Limit to first 5 to save API calls
                try:
                    llm_result = self.llm.generate_prediction_explanation(
                        home_team=pred.home_team,
                        away_team=pred.away_team,
                        home_win_prob=pred.outcome.home_win,
                        draw_prob=pred.outcome.draw,
                        away_win_prob=pred.outcome.away_win,
                        factors=[f.to_dict() if hasattr(f, 'to_dict') else f for f in pred.factors[:3]],
                    )
                    if llm_result.success:
                        self.state.llm_reasoning[pred.match_id] = llm_result.content
                        self._log_msg(f"  LLM reasoning for {pred.home_team} vs {pred.away_team}: OK")
                except Exception as e:
                    self._log_msg(f"  LLM reasoning failed: {e}")

            self.state.llm_latency_ms = (
                datetime.now(timezone.utc) - llm_start
            ).total_seconds() * 1000

        # Build snapshot
        snap_id = f"snap_{datetime.now(timezone.utc):%Y_%m_%d_%H%M}"

        # Detect changes vs previous snapshot
        changes = []
        try:
            prev_snapshots = sorted(SNAPSHOT_DIR.glob("snap_*.json"))
            if prev_snapshots:
                prev_path = prev_snapshots[-1]
                prev_snap = PredictionSnapshot.from_dict(
                    json.loads(prev_path.read_text(encoding="utf-8"))
                )
                changes = self._detect_changes(match_predictions, prev_snap.match_predictions)
        except Exception:
            pass

        # Headline generation
        top_change = changes[0] if changes else None
        headline = self._generate_headline(match_predictions, changes, top_change)

        snapshot = PredictionSnapshot(
            snapshot_id=snap_id,
            match_predictions=match_predictions,
            changes_from_previous=changes,
            headline=headline,
            prediction_version=get_pipeline_version(),
            knowledge_version=get_knowledge_version(),
        )

        save_snapshot(snapshot)
        self._log_msg(f"Saved snapshot: {snap_id} ({len(match_predictions)} matches)")
        return snapshot

    def _match_has_result(self, home: str, away: str) -> bool:
        """Check if a match already has a real result."""
        if not self.world_state:
            return False
        for result in self.world_state.results:
            if (result.home_team == home and result.away_team == away) or \
               (result.home_team == away and result.away_team == home):
                return True
        return False

    def _compute_probability_adjustment(
        self,
        home: str,
        away: str,
        outcome: OutcomeProbability,
    ) -> float:
        """
        Compute probability adjustment based on WorldState factors.

        Returns adjustment to add to home_win probability.
        """
        if not self.world_state:
            return 0.0

        home_state = self.world_state.teams.get(home)
        away_state = self.world_state.teams.get(away)

        adjustment = 0.0

        # Form adjustment
        if home_state and away_state:
            form_diff = home_state.strength_multiplier - away_state.strength_multiplier
            adjustment += form_diff * 0.1  # Max ±10% from form

        # Injury adjustment
        if away_state and away_state.injury_impact < 0:
            adjustment -= abs(away_state.injury_impact) * 0.05

        if home_state and home_state.injury_impact < 0:
            adjustment += home_state.injury_impact * 0.05

        return adjustment

    def _detect_changes(
        self,
        current: list[MatchPrediction],
        previous: list[MatchPrediction],
    ) -> list[dict]:
        """Identify probability changes between two snapshots."""
        changes = []
        prev_map = {m.match_id: m for m in previous}
        for curr in current:
            if curr.match_id not in prev_map:
                continue
            prev = prev_map[curr.match_id]
            for label, va, vb in [
                ("home_win", prev.outcome.home_win, curr.outcome.home_win),
                ("draw",     prev.outcome.draw,     curr.outcome.draw),
                ("away_win", prev.outcome.away_win, curr.outcome.away_win),
            ]:
                delta = vb - va
                if abs(delta) > 0.005:
                    changes.append({
                        "match_id": curr.match_id,
                        "teams": f"{curr.home_team} vs {curr.away_team}",
                        "metric": label,
                        "prev": round(va, 4),
                        "curr": round(vb, 4),
                        "delta_pct": round(delta * 100, 2),
                        "direction": "↑" if delta > 0 else "↓",
                    })
        changes.sort(key=lambda c: abs(c["delta_pct"]), reverse=True)
        return changes

    def _generate_headline(
        self,
        matches: list[MatchPrediction],
        changes: list[dict],
        top_change: dict | None,
    ) -> str:
        """Generate the daily briefing headline."""
        if not matches:
            return "No matches available for prediction today."

        # Find biggest upset (highest P_away_win where away is historically weaker)
        upset = None
        for m in matches:
            if m.outcome.away_win > 0.30:
                if upset is None or m.outcome.away_win > upset.outcome.away_win:
                    upset = m

        if upset:
            upset_str = (
                f"Upset watch: {upset.away_team} has a "
                f"{upset.outcome.away_win:.0%} chance of beating {upset.home_team} "
                f"(confidence: {upset.outcome.confidence})"
            )
        else:
            upset_str = "No significant upsets predicted today."

        if top_change:
            chg_str = (
                f"Biggest shift: {top_change['teams']} {top_change['metric']} "
                f"changed {top_change['direction']}{abs(top_change['delta_pct']):.1f}pp "
                f"(was {top_change['prev']:.0%}, now {top_change['curr']:.0%})"
            )
        else:
            chg_str = "No significant probability shifts since last snapshot."

        return f"{upset_str}. {chg_str}"

    @property
    def reasoning_trace(self) -> list[str]:
        """Returns the full agent reasoning trace for audit."""
        return self._log


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="WC2026 Prediction Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single prediction
  python -m worldcup_agent.prediction.agent

  # Force refresh data
  python -m worldcup_agent.prediction.agent --force-refresh

  # Compare with previous snapshot
  python -m worldcup_agent.prediction.agent --compare

  # Run in closed-loop mode (production)
  python -m worldcup_agent.prediction.agent --loop --interval 3600

  # Run closed-loop for testing (5 iterations)
  python -m worldcup_agent.prediction.agent --loop --max-iterations 5 --interval 10
"""
    )
    parser.add_argument("--force-refresh", action="store_true",
                        help="Force Elo refresh even if cache is fresh")
    parser.add_argument("--compare", action="store_true",
                        help="Show changes vs previous snapshot")
    parser.add_argument("--quiet", action="store_true", help="Suppress log output")
    parser.add_argument("--loop", action="store_true",
                        help="Run in continuous closed-loop mode (production)")
    parser.add_argument("--interval", type=int, default=3600,
                        help="Loop interval in seconds (default: 3600 = 1 hour)")
    parser.add_argument("--max-iterations", type=int, default=None,
                        help="Max iterations for loop mode (default: unlimited)")
    args = parser.parse_args()

    agent = WC2026Agent(force_refresh=args.force_refresh, verbose=not args.quiet)

    if args.loop:
        # Closed-loop mode
        agent.run_loop(interval=args.interval, max_iterations=args.max_iterations)
    else:
        # Single run mode
        snapshot = agent.run()

        print("\n" + "=" * 60)
        print("WC2026 DAILY FOOTBALL INTELLIGENCE")
        print(f"Snapshot: {snapshot.snapshot_id}")
        print(f"Generated: {snapshot.generated_at}")
        print(f"Prediction version: {snapshot.prediction_version}")
        print(f"Knowledge version: {snapshot.knowledge_version}")
        print(f"Matches: {len(snapshot.match_predictions)}")
        print("=" * 60)
        print(f"\n{snapshot.headline}")

        if snapshot.changes_from_previous:
            print(f"\n── Changes since last snapshot ({len(snapshot.changes_from_previous)} changes) ──")
            for chg in snapshot.changes_from_previous[:5]:
                print(f"  {chg['teams']} | {chg['metric']}: "
                      f"{chg['prev']:.0%} → {chg['curr']:.0%} ({chg['direction']}{abs(chg['delta_pct']):.1f}pp)")

        print("\n── Sample predictions ──")
        for m in snapshot.match_predictions[:3]:
            print(f"  {m.home_team} vs {m.away_team}")
            print(f"    H: {m.outcome.home_win:.0%}  D: {m.outcome.draw:.0%}  A: {m.outcome.away_win:.0%}")
            if m.factors:
                top = m.factors[0]
                print(f"    Top factor: {top.name} ({top.contribution_pct:.0%}) → {top.evidence}")
            print()

        print(f"  Snapshot saved: {SNAPSHOT_DIR / f'{snapshot.snapshot_id}.json'}")


if __name__ == "__main__":
    main()
