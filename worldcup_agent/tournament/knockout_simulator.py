"""FIFA World Cup 2026 — Knockout Simulator.

Block: ENGINE
Simulates R16 → QF → SF → third_place → final using probability model.
Each match output includes Reason + Evidence (Explainability block).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

from worldcup_agent.tournament.rule import KNOCKOUT_ORDER
from worldcup_agent.tournament.r32_builder import MatchTrace


# ── Knockout match output ──────────────────────────────────────────────────────

@dataclass
class KnockoutMatch:
    """One knockout stage match with probability and reasoning."""
    stage: str                      # "round_of_16", "quarter_final", ...
    match_id: str                   # e.g. "r16_00", "qf_00"
    round_index: int                # 0-based within stage
    home_team: str
    away_team: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    confidence: Literal["high", "medium", "low"] = "medium"
    predicted_winner: str | None = None
    reasoning: str = ""

    def __post_init__(self):
        spread = max(self.home_win_prob, self.draw_prob, self.away_win_prob) - \
                 min(self.home_win_prob, self.draw_prob, self.away_win_prob)
        if spread > 0.45:
            self.confidence = "high"
        elif spread > 0.20:
            self.confidence = "medium"
        else:
            self.confidence = "low"

        probs = {"home": self.home_win_prob, "draw": self.draw_prob, "away": self.away_win_prob}
        winner_key = max(probs, key=probs.get)
        self.predicted_winner = (
            self.home_team if winner_key == "home"
            else self.away_team if winner_key == "away"
            else None
        )

    def as_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "stage": self.stage,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_win_prob": round(self.home_win_prob, 4),
            "draw_prob": round(self.draw_prob, 4),
            "away_win_prob": round(self.away_win_prob, 4),
            "confidence": self.confidence,
            "predicted_winner": self.predicted_winner,
            "reasoning": self.reasoning,
        }


@dataclass
class KnockoutResult:
    """Complete tournament knockout simulation result."""
    champion: str
    runner_up: str
    third_place: str
    final: dict
    third_place_match: dict
    quarter_finals: list[dict]
    semi_finals: list[dict]
    round_of_16: list[dict]
    champion_probability: float = 1.0

    def summary(self) -> dict:
        return {
            "champion": self.champion,
            "runner_up": self.runner_up,
            "third_place": self.third_place,
            "champion_probability": self.champion_probability,
            "knockout_bracket": {
                "round_of_16": self.round_of_16,
                "quarter_finals": self.quarter_finals,
                "semi_finals": self.semi_finals,
                "third_place": self.third_place_match,
                "final": self.final,
            },
        }


# ── Bracket structure for 2026 (32→16→8→4→2→2→1) ─────────────────────────────

# R32 winner advances to R16 opponent position
R32_TO_R16_MAP = {
    # Upper half (matches r32_00..r32_07 → r16_00..r16_03 top, r16_04..r16_07 bottom)
    0: 0,   # r32_00 winner → r16_00
    1: 0,   # r32_01 winner → r16_00
    2: 1,   # r32_02 winner → r16_01
    3: 1,   # r32_03 winner → r16_01
    4: 2,   # r32_04 winner → r16_02
    5: 2,   # r32_05 winner → r16_02
    6: 3,   # r32_06 winner → r16_03
    7: 3,   # r32_07 winner → r16_03
    # Lower half
    8: 4,   # r32_08 winner → r16_04
    9: 4,   # r32_09 winner → r16_04
    10: 5,  # r32_10 winner → r16_05
    11: 5,  # r32_11 winner → r16_05
    12: 6,  # r32_12 winner → r16_06
    13: 6,  # r32_13 winner → r16_06
    14: 7,  # r32_14 winner → r16_07
    15: 7,  # r32_15 winner → r16_07
}

R16_TO_QF_MAP = {
    0: 0, 1: 0,   # r16_00/01 winner → qf_00
    2: 1, 3: 1,   # r16_02/03 winner → qf_01
    4: 2, 5: 2,   # r16_04/05 winner → qf_02
    6: 3, 7: 3,   # r16_06/07 winner → qf_03
}

QF_TO_SF_MAP = {
    0: 0, 1: 0,   # qf_00/01 winner → sf_00
    2: 1, 3: 1,   # qf_02/03 winner → sf_01
}

SF_TO_FINAL_MAP = {
    # Winners advance to final
    0: 0,   # sf_00 winner → final
    1: 0,   # sf_01 winner → final
}

SF_TO_THIRD_MAP = {
    # Losers advance to third place match
    0: 1,   # sf_00 loser → third_place
    1: 1,   # sf_01 loser → third_place
}


# ── Probability model ──────────────────────────────────────────────────────────

# Default Elo ratings used when team-specific data not available
DEFAULT_ELO = 1500


class EloProbModel:
    """
    Simple Elo-based probability model for knockout simulation.

    Accepts optional team_elo_map to override defaults.
    """

    def __init__(self, team_elo_map: dict[str, int] | None = None):
        self.team_elo = team_elo_map or {}

    def expected_score(self, elo_a: float, elo_b: float) -> tuple[float, float, float]:
        """Return (win_a, draw, win_b) probabilities from Elo ratings."""
        diff = elo_a - elo_b
        # Logistic model: P(A beats B) = 1 / (1 + 10^(diff/400))
        p_win = 1.0 / (1.0 + 10 ** (diff / 400))
        # Draw probability model (simplified)
        p_draw = 0.25 * (1.0 - abs(diff) / 800)
        p_draw = max(0.10, min(0.28, p_draw))
        p_win = max(0.05, min(0.85, p_win))
        p_draw = min(p_draw, 1.0 - p_win - 0.05)
        p_loss = 1.0 - p_win - p_draw
        return p_win, p_draw, p_loss

    def match_prob(
        self,
        home_team: str,
        away_team: str,
    ) -> tuple[float, float, float]:
        """Return (home_win, draw, away_win) for a match."""
        h_elo = float(self.team_elo.get(home_team, DEFAULT_ELO))
        a_elo = float(self.team_elo.get(away_team, DEFAULT_ELO))
        return self.expected_score(h_elo, a_elo)


# ── Main simulator ─────────────────────────────────────────────────────────────

class KnockoutSimulator:
    """
    Simulate full knockout bracket from R32 traces.

    Block: ENGINE
    - Takes R32 MatchTrace list
    - Uses probability model to predict winners
    - Produces complete bracket with reasoning
    """

    def __init__(
        self,
        elo_model: EloProbModel | None = None,
        seed: int | None = None,
    ):
        self.elo = elo_model or EloProbModel()
        self.rng = random.Random(seed)

    def _make_match(
        self,
        stage: str,
        match_id: str,
        home: str,
        away: str,
    ) -> KnockoutMatch:
        h_win, draw, a_win = self.elo.match_prob(home, away)

        # Build reasoning
        h_elo = self.elo.team_elo.get(home, DEFAULT_ELO)
        a_elo = self.elo.team_elo.get(away, DEFAULT_ELO)
        diff = h_elo - a_elo
        if abs(diff) > 100:
            reason = f"Elo gap of {diff:+.0f} points — {'home' if diff > 0 else 'away'} advantage"
        elif abs(diff) > 50:
            reason = f"Close matchup (Elo diff {diff:+.0f}) — slight edge to {'home' if diff > 0 else 'away'}"
        else:
            reason = "Evenly matched teams — high uncertainty"

        return KnockoutMatch(
            stage=stage,
            match_id=match_id,
            round_index=0,
            home_team=home,
            away_team=away,
            home_win_prob=h_win,
            draw_prob=draw,
            away_win_prob=a_win,
            reasoning=reason,
        )

    def _advance(
        self,
        bracket: list[KnockoutMatch],
        mapping: dict[int, int],
    ) -> dict[int, KnockoutMatch]:
        """Advance winners to next round based on bracket mapping."""
        next_round: dict[int, KnockoutMatch] = {}
        for r32_idx, r16_slot in mapping.items():
            if r32_idx >= len(bracket):
                continue
            winner = bracket[r32_idx].predicted_winner
            if winner is None:
                # Draw — pick by higher Elo
                m = bracket[r32_idx]
                h_elo = self.elo.team_elo.get(m.home_team, DEFAULT_ELO)
                a_elo = self.elo.team_elo.get(m.away_team, DEFAULT_ELO)
                winner = m.home_team if h_elo >= a_elo else m.away_team
            next_round.setdefault(r16_slot, winner)
        return next_round

    def simulate(self, r32_traces: list[MatchTrace]) -> KnockoutResult:
        """
        Simulate full knockout: R32 → R16 → QF → SF → third → final.

        Returns champion, runner_up, third_place + full bracket.
        """
        if len(r32_traces) < 16:
            raise ValueError(f"Need 16 R32 matches, got {len(r32_traces)}")

        # Build R32 matches with probabilities
        r32_matches: list[KnockoutMatch] = []
        for i, trace in enumerate(r32_traces[:16]):
            r32_matches.append(
                KnockoutMatch(
                    stage="round_of_32",
                    match_id=f"r32_{i:02d}",
                    round_index=i,
                    home_team=trace.home_team,
                    away_team=trace.away_team,
                    home_win_prob=0.5,
                    draw_prob=0.2,
                    away_win_prob=0.3,
                    reasoning="R32 from ConstraintR32Engine",
                )
            )
            # Compute real prob
            h_win, draw, a_win = self.elo.match_prob(trace.home_team, trace.away_team)
            r32_matches[-1].home_win_prob = h_win
            r32_matches[-1].draw_prob = draw
            r32_matches[-1].away_win_prob = a_win

        # R16
        r16_dict = self._advance(r32_matches, R32_TO_R16_MAP)
        r16_matches: list[KnockoutMatch] = []
        for slot, winner_home in sorted(r16_dict.items()):
            # Reconstruct home/away for this slot
            slot_winners = [
                (idx, m.predicted_winner)
                for idx, m in enumerate(r32_matches)
                if R32_TO_R16_MAP.get(idx) == slot
                and m.predicted_winner is not None
            ]
            if len(slot_winners) == 2:
                h = slot_winners[0][1]
                a = slot_winners[1][1]
            elif len(slot_winners) == 1:
                h = slot_winners[0][1]
                a = "TBD"
            else:
                h = "TBD"
                a = "TBD"
            m = self._make_match("round_of_16", f"r16_{slot:02d}", h, a)
            m.round_index = slot
            r16_matches.append(m)

        # QF
        qf_dict = self._advance(r16_matches, R16_TO_QF_MAP)
        qf_matches: list[KnockoutMatch] = []
        for slot, winner_home in sorted(qf_dict.items()):
            slot_matches = [m for m in r16_matches if m.round_index in
                           [k for k, v in R16_TO_QF_MAP.items() if v == slot]]
            if len(slot_matches) == 2:
                h = slot_matches[0].predicted_winner or slot_matches[0].home_team
                a = slot_matches[1].predicted_winner or slot_matches[1].away_team
            else:
                h, a = "TBD", "TBD"
            m = self._make_match("quarter_final", f"qf_{slot:02d}", h, a)
            m.round_index = slot
            qf_matches.append(m)

        # SF
        sf_dict = self._advance(qf_matches, QF_TO_SF_MAP)
        sf_matches: list[KnockoutMatch] = []
        for slot, winner_home in sorted(sf_dict.items()):
            slot_matches = [m for m in qf_matches if m.round_index in
                           [k for k, v in QF_TO_SF_MAP.items() if v == slot]]
            if len(slot_matches) == 2:
                h = slot_matches[0].predicted_winner or slot_matches[0].home_team
                a = slot_matches[1].predicted_winner or slot_matches[1].away_team
            else:
                h, a = "TBD", "TBD"
            m = self._make_match("semi_final", f"sf_{slot:02d}", h, a)
            m.round_index = slot
            sf_matches.append(m)

        # Third place
        sf0_loser = self._loser(sf_matches[0])
        sf1_loser = self._loser(sf_matches[1])
        third_match = self._make_match(
            "third_place", "third", sf0_loser, sf1_loser
        )
        third_place = third_match.predicted_winner or sf0_loser

        # Final
        sf0_winner = sf_matches[0].predicted_winner or sf_matches[0].home_team
        sf1_winner = sf_matches[1].predicted_winner or sf_matches[1].away_team
        final_match = self._make_match("final", "final", sf0_winner, sf1_winner)
        champion = final_match.predicted_winner or sf0_winner
        runner_up = sf1_winner if champion == sf0_winner else sf0_winner

        return KnockoutResult(
            champion=champion,
            runner_up=runner_up,
            third_place=third_place,
            final=final_match.as_dict(),
            third_place_match=third_match.as_dict(),
            quarter_finals=[m.as_dict() for m in qf_matches],
            semi_finals=[m.as_dict() for m in sf_matches],
            round_of_16=[m.as_dict() for m in r16_matches],
            champion_probability=1.0,
        )

    def _loser(self, m: KnockoutMatch) -> str:
        winner = m.predicted_winner
        if winner == m.home_team:
            return m.away_team
        elif winner == m.away_team:
            return m.home_team
        return m.home_team
