"""Debate Mechanism — Multi-Agent Adversarial Collaboration.

This module implements structured debate between agents to:

1. DETECT CONFLICTS: When agents disagree on a prediction/analysis
2. STRUCTURE DEBATE: Define positions, arguments, rebuttals
3. RESOLVE CONFLICTS: Use structured reasoning to resolve disagreements
4. LEVERAGE DIVERGENCE: Turn disagreements into better predictions

Key principle:
  "Multiple perspectives improve prediction quality"
  vs the old: "Single-path reasoning"
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from worldcup_agent.multi_agent.cognitive_model import (
    CognitiveWorldModel,
    Belief,
    ConflictRecord,
)


# ── Debate Types ──────────────────────────────────────────────────────────────


class DebateStatus(Enum):
    """Status of a debate."""
    PROPOSED = "proposed"
    OPEN = "open"
    ARGUMENTS_PRESENTED = "arguments_presented"
    REBUTTALS_EXCHANGED = "rebuttals_exchanged"
    RESOLVED = "resolved"
    STALEMATE = "stalemate"


class PositionSide(Enum):
    """Which side of the debate."""
    PRO = "pro"      # Supports the original belief
    CON = "con"     # Challenges the original belief
    NEUTRAL = "neutral"  # Evaluating/judging


class ArgumentStrength(Enum):
    """Strength of an argument."""
    STRONG = "strong"      # High confidence, good evidence
    MODERATE = "moderate"  # Decent reasoning
    WEAK = "weak"         # Low confidence, weak evidence


# ── Debate Data Classes ───────────────────────────────────────────────────────


@dataclass
class Argument:
    """
    A single argument in a debate.

    Structure:
      - Claim: What the agent believes
      - Evidence: Why the agent believes it
      - Confidence: How confident the agent is
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_id: str
    side: PositionSide

    # Content
    claim: str                     # What the agent asserts
    evidence: list[str] = field(default_factory=list)  # Supporting evidence
    reasoning: str = ""            # Chain of reasoning

    # Confidence
    strength: ArgumentStrength = ArgumentStrength.MODERATE
    confidence: float = 0.5       # 0-1

    # Meta
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_rebuttal: bool = False      # Is this a rebuttal?
    targets_argument_id: str | None = None  # Which argument it rebuts

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "side": self.side.value,
            "claim": self.claim,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "strength": self.strength.value,
            "confidence": round(self.confidence, 4),
            "is_rebuttal": self.is_rebuttal,
            "targets_argument_id": self.targets_argument_id,
            "timestamp": self.timestamp,
        }


@dataclass
class DebateRound:
    """
    One round of a debate.

    A debate can have multiple rounds:
      Round 1: Opening arguments (PRO and CON)
      Round 2: Rebuttals
      Round 3: (Optional) Surrebuttals
      ...
      Final: Judge's verdict
    """
    round_number: int
    arguments: list[Argument] = field(default_factory=list)
    opened_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    closed_at: str | None = None

    def add_argument(self, arg: Argument) -> None:
        self.arguments.append(arg)

    def get_arguments_for(self, side: PositionSide) -> list[Argument]:
        return [a for a in self.arguments if a.side == side]

    def to_dict(self) -> dict:
        return {
            "round_number": self.round_number,
            "arguments": [a.to_dict() for a in self.arguments],
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
        }


@dataclass
class Debate:
    """
    A structured debate between agents.

    This is the core of the debate mechanism - it structures
    disagreements into a formal debate format.

    Structure:
      1. Topic: What the debate is about
      2. Proponent: Agent proposing a belief
      3. Opponent: Agent challenging the belief
      4. Rounds: Arguments and rebuttals
      5. Verdict: How the debate was resolved
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Topic
    topic: str                     # e.g., "Argentina champion probability > 30%"
    subject: str                  # Belief subject
    predicate: str                # Belief predicate

    # Participants
    proponent: str                 # Agent proposing the belief
    opponent: str | None = None   # Agent challenging the belief
    judge: str = "reflection_agent"  # Agent that judges

    # Status
    status: DebateStatus = DebateStatus.PROPOSED
    current_round: int = 0
    max_rounds: int = 3

    # Rounds
    rounds: list[DebateRound] = field(default_factory=list)

    # Verdict
    verdict: str | None = None
    verdict_confidence: float = 0.0
    winner: str | None = None
    reasoning: str | None = None

    # Meta
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str | None = None

    def open_debate(self) -> DebateRound:
        """Start the first round of debate."""
        self.status = DebateStatus.OPEN
        round_1 = DebateRound(round_number=1)
        self.rounds.append(round_1)
        self.current_round = 1
        return round_1

    def next_round(self) -> DebateRound | None:
        """Start the next round."""
        if self.current_round >= self.max_rounds:
            return None

        self.current_round += 1
        round_n = DebateRound(round_number=self.current_round)
        self.rounds.append(round_n)

        # Update status
        if self.current_round == self.max_rounds:
            self.status = DebateStatus.REBUTTALS_EXCHANGED

        return round_n

    def close_debate(self, verdict: str, winner: str, reasoning: str, confidence: float) -> None:
        """Close the debate with a verdict."""
        self.status = DebateStatus.RESOLVED
        self.verdict = verdict
        self.winner = winner
        self.reasoning = reasoning
        self.verdict_confidence = confidence
        self.resolved_at = datetime.now(timezone.utc).isoformat()

        for round_ in self.rounds:
            if round_.closed_at is None:
                round_.closed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "subject": self.subject,
            "predicate": self.predicate,
            "proponent": self.proponent,
            "opponent": self.opponent,
            "judge": self.judge,
            "status": self.status.value,
            "current_round": self.current_round,
            "rounds": [r.to_dict() for r in self.rounds],
            "verdict": self.verdict,
            "winner": self.winner,
            "verdict_confidence": round(self.verdict_confidence, 4),
            "reasoning": self.reasoning,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


# ── Debate Manager ───────────────────────────────────────────────────────────


class DebateManager:
    """
    Manages debates between agents.

    This is the orchestrator of the debate mechanism - it:
      1. Detects conflicts that need debates
      2. Initiates debates
      3. Coordinates rounds
      4. Produces verdicts
      5. Updates beliefs based on verdict
    """

    def __init__(self, cognitive_model: CognitiveWorldModel):
        self.cognitive_model = cognitive_model
        self.active_debates: dict[str, Debate] = {}
        self.resolved_debates: dict[str, Debate] = {}
        self.debate_history: list[Debate] = []

    # ── Conflict Detection ───────────────────────────────────────────────

    def detect_conflicts(self) -> list[ConflictRecord]:
        """
        Detect conflicts in the cognitive model that need debate.

        Returns list of conflicts that should be debated.
        """
        return [
            c for c in self.cognitive_model.conflicts
            if not c.is_resolved
            and c.divergence > 0.10  # > 10% divergence requires debate
        ]

    def should_debate(self, conflict: ConflictRecord) -> bool:
        """
        Decide if a conflict should trigger a debate.

        Criteria:
          - High divergence (>15%)
          - Low confidence in either belief
          - Both agents have strong evidence
        """
        belief_a = self.cognitive_model.beliefs.get(conflict.belief_a_id)

        if conflict.divergence < 0.15:
            return False  # Too low divergence

        if belief_a and belief_a.confidence < 0.5:
            return True  # Low confidence needs debate

        if belief_a and len(belief_a.evidence) < 2:
            return False  # Not enough evidence to debate

        return True

    # ── Debate Initiation ───────────────────────────────────────────────

    def initiate_debate(
        self,
        topic: str,
        subject: str,
        predicate: str,
        proponent: str,
    ) -> Debate:
        """
        Start a new debate on a topic.

        This is typically called when:
          - A conflict is detected
          - An agent wants to challenge another agent's belief
          - A low-confidence belief needs validation
        """
        debate = Debate(
            topic=topic,
            subject=subject,
            predicate=predicate,
            proponent=proponent,
        )

        self.active_debates[debate.id] = debate
        return debate

    def add_opponent(self, debate_id: str, opponent: str) -> None:
        """Add an opponent to a debate."""
        debate = self.active_debates.get(debate_id)
        if debate:
            debate.opponent = opponent
            debate.open_debate()

    # ── Argument Submission ─────────────────────────────────────────────

    def submit_argument(
        self,
        debate_id: str,
        agent_id: str,
        side: PositionSide,
        claim: str,
        evidence: list[str],
        reasoning: str,
        confidence: float = 0.5,
        is_rebuttal: bool = False,
        targets_argument_id: str | None = None,
    ) -> Argument | None:
        """Submit an argument in a debate."""
        debate = self.active_debates.get(debate_id)
        if not debate or debate.status == DebateStatus.RESOLVED:
            return None

        # Create argument
        arg = Argument(
            agent_id=agent_id,
            side=side,
            claim=claim,
            evidence=evidence,
            reasoning=reasoning,
            confidence=confidence,
            is_rebuttal=is_rebuttal,
            targets_argument_id=targets_argument_id,
        )

        # Add to current round
        if not debate.rounds:
            debate.open_debate()

        current_round = debate.rounds[-1]
        current_round.add_argument(arg)

        # Update debate status
        if is_rebuttal:
            debate.status = DebateStatus.REBUTTALS_EXCHANGED

        return arg

    # ── Debate Resolution ───────────────────────────────────────────────

    def judge_debate(self, debate_id: str) -> Debate | None:
        """
        Judge a debate and produce a verdict.

        The judge (Reflection Agent) evaluates:
          1. Strength of evidence
          2. Quality of reasoning
          3. Confidence levels
          4. Rebuttal effectiveness
        """
        debate = self.active_debates.get(debate_id)
        if not debate:
            return None

        # Gather all arguments
        pro_args = []
        con_args = []
        for round_ in debate.rounds:
            pro_args.extend(round_.get_arguments_for(PositionSide.PRO))
            con_args.extend(round_.get_arguments_for(PositionSide.CON))

        if not pro_args or not con_args:
            # Need both sides
            debate.status = DebateStatus.STALEMATE
            debate.verdict = "Inconclusive: insufficient arguments"
            debate.verdict_confidence = 0.3
            return debate

        # Calculate scores
        pro_score = self._calculate_score(pro_args)
        con_score = self._calculate_score(con_args)

        # Determine winner
        if pro_score > con_score * 1.2:  # Pro needs 20% advantage
            winner = "pro"
            verdict_confidence = min(0.95, pro_score)
        elif con_score > pro_score * 1.2:
            winner = "con"
            verdict_confidence = min(0.95, con_score)
        else:
            # Too close - use weighted average
            winner = "tie"
            verdict_confidence = (pro_score + con_score) / 2

        # Generate verdict reasoning
        reasoning = self._generate_verdict_reasoning(pro_args, con_args, winner, pro_score, con_score)

        # Close debate
        debate.close_debate(
            verdict=f"VERDICT: {'PRO' if winner == 'pro' else 'CON' if winner == 'con' else 'TIE'}",
            winner=winner,
            reasoning=reasoning,
            confidence=verdict_confidence,
        )

        # Move to resolved
        self.resolved_debates[debate.id] = debate
        if debate.id in self.active_debates:
            del self.active_debates[debate.id]
        self.debate_history.append(debate)

        # Update cognitive model based on verdict
        self._apply_verdict(debate)

        return debate

    def _calculate_score(self, arguments: list[Argument]) -> float:
        """Calculate weighted score for arguments."""
        if not arguments:
            return 0.0

        total = 0.0
        for arg in arguments:
            # Base score from confidence
            base = arg.confidence

            # Strength multiplier
            strength_mult = {
                ArgumentStrength.STRONG: 1.0,
                ArgumentStrength.MODERATE: 0.7,
                ArgumentStrength.WEAK: 0.4,
            }.get(arg.strength, 0.5)

            # Rebuttal bonus
            rebuttal_bonus = 0.2 if arg.is_rebuttal else 0.0

            # Evidence count bonus
            evidence_bonus = min(0.1, len(arg.evidence) * 0.02)

            total += base * strength_mult + rebuttal_bonus + evidence_bonus

        return min(1.0, total / len(arguments))

    def _generate_verdict_reasoning(
        self,
        pro_args: list[Argument],
        con_args: list[Argument],
        winner: str,
        pro_score: float,
        con_score: float,
    ) -> str:
        """Generate human-readable verdict reasoning."""
        if winner == "pro":
            reason = f"PRO prevails with score {pro_score:.2f} vs CON {con_score:.2f}. "
            # Find strongest PRO argument
            strongest = max(pro_args, key=lambda a: a.confidence * (1.2 if a.is_rebuttal else 1.0))
            reason += f"Strongest argument: {strongest.claim}"
        elif winner == "con":
            reason = f"CON prevails with score {con_score:.2f} vs PRO {pro_score:.2f}. "
            strongest = max(con_args, key=lambda a: a.confidence * (1.2 if a.is_rebuttal else 1.0))
            reason += f"Strongest argument: {strongest.claim}"
        else:
            reason = f"TIE: PRO {pro_score:.2f} vs CON {con_score:.2f}. "
            reason += "Arguments are equally compelling. Using weighted average."

        return reason

    def _apply_verdict(self, debate: Debate) -> None:
        """Apply debate verdict to cognitive model."""
        belief_id = f"{debate.subject}:{debate.predicate}"
        belief = self.cognitive_model.beliefs.get(belief_id)

        if not belief:
            return

        # Update belief based on verdict
        if debate.winner == "pro":
            # PRO won - strengthen belief
            belief.confidence = min(1.0, belief.confidence * 1.1)
            belief.is_verified = True
        elif debate.winner == "con":
            # CON won - weaken belief, mark as contested
            belief.confidence = belief.confidence * 0.9
            belief.is_contested = True
            belief.conflict_source = debate.opponent
        else:
            # Tie - mark for review
            belief.is_verified = False

    # ── Convenience Methods ─────────────────────────────────────────────

    def debate_prediction(
        self,
        subject: str,
        predicate: str,
        proponent: str,
        opponent: str,
        pro_value: Any,
        con_value: Any,
    ) -> Debate:
        """
        Convenience method to debate a prediction.

        Automatically:
          1. Creates debate
          2. Adds both agents
          3. Opens debate
          4. Submits initial arguments
        """
        topic = f"{subject}:{predicate} — {proponent} vs {opponent}"

        debate = self.initiate_debate(
            topic=topic,
            subject=subject,
            predicate=predicate,
            proponent=proponent,
        )
        debate.opponent = opponent
        debate.open_debate()

        # Submit PRO argument
        self.submit_argument(
            debate_id=debate.id,
            agent_id=proponent,
            side=PositionSide.PRO,
            claim=f"{predicate} = {pro_value}",
            evidence=[f"Agent {proponent} calculated value"],
            reasoning=f"Based on analysis by {proponent}",
            confidence=0.7,
        )

        # Submit CON argument
        self.submit_argument(
            debate_id=debate.id,
            agent_id=opponent,
            side=PositionSide.CON,
            claim=f"{predicate} ≠ {pro_value}",
            evidence=[f"Agent {opponent} calculated different value: {con_value}"],
            reasoning=f"Disagrees: {opponent} analysis suggests {con_value}",
            confidence=0.6,
        )

        return debate

    # ── Query Methods ───────────────────────────────────────────────────

    def get_active_debates(self) -> list[Debate]:
        """Get all active debates."""
        return list(self.active_debates.values())

    def get_debate_for(self, subject: str, predicate: str) -> Debate | None:
        """Get the active debate for a belief."""
        for debate in self.active_debates.values():
            if debate.subject == subject and debate.predicate == predicate:
                return debate
        return None

    def to_dict(self) -> dict:
        return {
            "active_debates": len(self.active_debates),
            "resolved_debates": len(self.resolved_debates),
            "active": [d.to_dict() for d in self.active_debates.values()],
        }
