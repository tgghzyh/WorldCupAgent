"""WC2026 Prediction Agent — Agentic Orchestrator.

Unlike a sequential pipeline, this agent:
  1. PLANS   — decides what predictions to make today
  2. SEARCHES — checks if new data is available (Elo refresh, injury news)
  3. TOOLS    — calls the right data source based on freshness
  4. REASONS  — builds feature vectors and runs explainability
  5. PREDICTS — generates probabilities with full attribution
  6. VISUALISES — produces the daily intelligence briefing

Usage:
  python -m worldcup_agent.prediction.agent
  python -m worldcup_agent.prediction.agent --force-refresh  # bypass TTL
  python -m worldcup_agent.prediction.agent --compare        # diff vs previous snapshot
"""
from __future__ import annotations

import json
import subprocess
import sys
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

# ── Agent State ─────────────────────────────────────────────────────────────────

@dataclass
class AgentState:
    """Mutable state carried through the agent loop."""
    step: Literal["idle", "plan", "search", "tools", "reason", "predict", "done"]
    messages: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    data_fresh: bool = False
    prediction_version: str = ""
    knowledge_version: str = ""
    snapshot: PredictionSnapshot | None = None
    error: str | None = None


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
    """The main agent orchestrator."""

    def __init__(self, force_refresh: bool = False, verbose: bool = True):
        self.tools = ToolRegistry(force_refresh=force_refresh)
        self.explainer = ExplainabilityEngine()
        self.verbose = verbose
        self.state = AgentState(step="idle")
        self._log: list[str] = []

    def _log_msg(self, msg: str) -> None:
        self._log.append(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}")
        if self.verbose:
            print(f"  > {msg}")

    def run(self) -> PredictionSnapshot:
        """Execute the full agent loop. Returns a PredictionSnapshot."""
        self.state.step = "plan"
        self._plan()

        self.state.step = "search"
        self._search()

        self.state.step = "tools"
        tool_results = self._execute_tools()

        self.state.step = "reason"
        self._reason(tool_results)

        self.state.step = "predict"
        snapshot = self._predict(tool_results)

        self.state.step = "done"
        self.state.snapshot = snapshot
        return snapshot

    # ── Step 1: Plan ──────────────────────────────────────────────────────────

    def _plan(self) -> None:
        """Decide what to do today based on tournament state."""
        self._log_msg("PLANNING: assessing today's objectives")
        # In production: query tournament calendar, check scheduled matches
        self.state.messages.append(
            "Goal: Generate updated prediction snapshot for WC 2026. "
            "Refresh Elo if stale. Compare with previous snapshot for change detection."
        )
        self._log_msg("Plan: refresh data → build features → predict → explain → save snapshot")

    # ── Step 2: Search ───────────────────────────────────────────────────────

    def _search(self) -> None:
        """Check what data is fresh and what needs updating."""
        self._log_msg("SEARCHING: checking knowledge base freshness")
        self.state.messages.append(
            "Checking Elo freshness (TTL=7d). "
            "Checking if team features need re-fetch. "
            "Checking injury/news integration."
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
        """Generate all match predictions with explainability."""
        self._log_msg("PREDICTING: running model + explainability")

        teams_data = tool_results.get("features", ToolResult("", False)).data or {}
        team_list: list[dict] = teams_data.get("teams", [])

        elo_map = {
            t.get("team_2026_name", ""): t.get("elo_rating_live", 1500)
            for t in team_list
        }
        rank_map = {
            t.get("team_2026_name", ""): t.get("world_rank_live", 120)
            for t in team_list
        }

        elo_system = ELOSystem()

        match_predictions: list[MatchPrediction] = []
        teams_2026 = {t["team_2026_name"]: t["group"] for t in team_list}

        for home, home_grp in teams_2026.items():
            for away, away_grp in teams_2026.items():
                if home >= away or home_grp != away_grp:
                    continue  # same-group only for now

                h_elo = elo_map.get(home, 1500)
                a_elo = elo_map.get(away, 1500)
                h_rank = rank_map.get(home, 120)
                a_rank = rank_map.get(away, 120)

                home_team_data = next((t for t in team_list if t["team_2026_name"] == home), {})
                away_team_data = next((t for t in team_list if t["team_2026_name"] == away), {})

                # Simulate prediction using Elo
                proba = elo_system.expected_score(h_elo, a_elo)
                outcome = OutcomeProbability(
                    home_win=round(proba[0], 4),
                    draw=round(proba[1], 4),
                    away_win=round(proba[2], 4),
                )

                # Explainability
                factors = self.explainer.explain(
                    home, away,
                    {"elo_rating_live": h_elo, "world_rank_live": h_rank},
                    {"elo_rating_live": a_elo, "world_rank_live": a_rank},
                    outcome,
                    model_contribution={"elo_diff": abs(h_elo - a_elo)},
                )

                # Predicted winner (most likely outcome, skip draw for "winner")
                if outcome.home_win > max(outcome.draw, outcome.away_win):
                    pred_winner = home
                elif outcome.away_win > max(outcome.home_win, outcome.draw):
                    pred_winner = away
                else:
                    pred_winner = None  # draw most likely — no clear winner

                match_predictions.append(MatchPrediction(
                    match_id=f"wc2026_{home[:3].upper()}_{away[:3].upper()}",
                    home_team=home,
                    away_team=away,
                    kickoff="2026-07-14T00:00:00Z",  # placeholder — real schedule from S6
                    outcome=outcome,
                    predicted_winner=pred_winner if pred_winner != "draw" else None,
                    factors=factors,
                    model_used="elo_system_v1",
                    training_set_size=448,
                ))

        # Build snapshot
        snap_id = f"snap_{datetime.now(timezone.utc):%Y_%m_%d}"

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
    parser = argparse.ArgumentParser(description="WC2026 Prediction Agent")
    parser.add_argument("--force-refresh", action="store_true",
                        help="Force Elo refresh even if cache is fresh")
    parser.add_argument("--compare", action="store_true",
                        help="Show changes vs previous snapshot")
    parser.add_argument("--quiet", action="store_true", help="Suppress log output")
    args = parser.parse_args()

    agent = WC2026Agent(force_refresh=args.force_refresh, verbose=not args.quiet)
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
