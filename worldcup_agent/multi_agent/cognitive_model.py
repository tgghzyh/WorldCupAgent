"""Cognitive World Model — Belief, Uncertainty, Evidence.

This module implements an advanced cognitive world model that upgrades
the simple WorldState into a proper Belief Model with:

1. BELIEF: Explicit representation of what the system "knows"
2. UNCERTAINTY: Explicit representation of uncertainty (epistemic + aleatoric)
3. EVIDENCE: Explicit evidence chains showing WHY a prediction was made
4. CONFIDENCE PROPAGATION: Uncertainty flows through the reasoning chain

This transforms the system from a "data repository" to a "cognitive model"
that can answer:
  - "Why did you predict X?"
  - "How confident are you?"
  - "What could change your mind?"
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal


# ── Evidence Types ────────────────────────────────────────────────────────────


class EvidenceSource(Enum):
    """Source of evidence for a belief."""
    ELO_RATING = "elo_rating"           # From Elo system
    FIFA_RANKING = "fifa_ranking"       # From FIFA rankings
    MATCH_HISTORY = "match_history"      # From historical matches
    SIMULATION = "simulation"            # From Monte Carlo simulation
    EXPERT_OPINION = "expert_opinion"    # From external sources
    FORM_ANALYSIS = "form_analysis"     # From recent form
    ODDS_MARKET = "odds_market"         # From betting odds
    INJURY_DATA = "injury_data"         # From injury reports
    AGENT_INFERENCE = "agent_inference"  # From other agent reasoning
    USER_INPUT = "user_input"           # From human input


class EvidenceQuality(Enum):
    """Quality of evidence (affects confidence)."""
    HIGH = "high"      # Direct, recent, reliable
    MEDIUM = "medium"  # Indirect or slightly outdated
    LOW = "low"       # Weak or unreliable


class UncertaintyType(Enum):
    """Type of uncertainty."""
    ALEATORIC = "aleatoric"    # Inherent randomness (football is unpredictable)
    EPISTEMIC = "epistemic"    # Lack of knowledge (could be reduced)
    MODEL = "model"           # Model uncertainty
    STAKEHOLDER = "stakeholder" # Subjective/game-theoretic uncertainty


# ── Core Data Classes ────────────────────────────────────────────────────────


@dataclass
class Evidence:
    """
    A single piece of evidence supporting a belief.

    Example:
        Evidence(
            source=EvidenceSource.ELO_RATING,
            content="Argentina Elo: 2151, France Elo: 2134",
            quality=EvidenceQuality.HIGH,
            weight=0.45,  # 45% of final confidence
            timestamp="2026-07-05T12:00:00Z",
            agent_id="analysis_agent",
        )
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: EvidenceSource
    content: str                    # Human-readable description
    quality: EvidenceQuality        # Quality of this evidence
    weight: float = 1.0            # Weight in final confidence (0-1)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_id: str | None = None    # Which agent produced this evidence
    provenance: str | None = None  # Chain ID linking to upstream evidence

    # Data quality indicators
    data_age_hours: float | None = None
    data_completeness: float = 1.0  # 0-1, how complete is this data?

    def confidence_contribution(self) -> float:
        """Calculate confidence contribution based on quality and weight."""
        quality_multiplier = {
            EvidenceQuality.HIGH: 1.0,
            EvidenceQuality.MEDIUM: 0.6,
            EvidenceQuality.LOW: 0.3,
        }.get(self.quality, 0.5)

        # Adjust for data freshness
        freshness = 1.0
        if self.data_age_hours:
            if self.data_age_hours > 168:  # > 7 days
                freshness = 0.5
            elif self.data_age_hours > 24:  # > 1 day
                freshness = 0.8

        # Adjust for completeness
        completeness = self.data_completeness

        return self.weight * quality_multiplier * freshness * completeness


@dataclass
class Belief:
    """
    A single belief in the cognitive model.

    Represents: "I believe X with confidence Y because of evidence Z"

    Example:
        Belief(
            subject="argentina_vs_france",
            predicate="home_win_prob",
            value=0.55,
            confidence=0.72,
            uncertainty={
                UncertaintyType.EPISTEMIC: 0.15,
                UncertaintyType.ALEATORIC: 0.13,
            },
            evidence=[
                Evidence(source=EvidenceSource.ELO_RATING, weight=0.45, ...),
                Evidence(source=EvidenceSource.SIMULATION, weight=0.35, ...),
            ],
        )
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # What this belief is about
    subject: str                     # e.g., "argentina_vs_france"
    predicate: str                    # e.g., "home_win_prob", "champion_prob"
    value: Any                        # The actual value

    # Confidence and uncertainty
    confidence: float = 0.5           # Overall confidence (0-1)
    uncertainty: dict[str, float] = field(default_factory=dict)
    # {uncertainty_type: magnitude}

    # Evidence chain
    evidence: list[Evidence] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_id: str | None = None     # Which agent formed this belief

    # Status
    is_verified: bool = False        # Has this been cross-checked?
    is_contested: bool = False       # Do other agents disagree?
    conflict_source: str | None = None

    def update_confidence(self) -> None:
        """Recalculate confidence based on evidence."""
        if not self.evidence:
            self.confidence = 0.5
            return

        total_confidence = sum(e.confidence_contribution() for e in self.evidence)
        self.confidence = min(1.0, total_confidence)

    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence and recalculate confidence."""
        self.evidence.append(evidence)
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.update_confidence()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "confidence": round(self.confidence, 4),
            "uncertainty": {k: round(v, 4) for k, v in self.uncertainty.items()},
            "evidence": [
                {
                    "source": e.source.value,
                    "content": e.content,
                    "quality": e.quality.value,
                    "weight": e.weight,
                    "confidence_contrib": round(e.confidence_contribution(), 4),
                }
                for e in self.evidence
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "agent_id": self.agent_id,
            "is_verified": self.is_verified,
            "is_contested": self.is_contested,
        }


@dataclass
class EvidenceChain:
    """
    A chain of reasoning showing how a conclusion was reached.

    Example:
        EvidenceChain(
            id="chain_001",
            root_belief_id="belief_123",
            conclusion="Argentina wins with 55% probability",
            steps=[
                ChainStep(
                    agent_id="data_agent",
                    action="fetch_elo",
                    result="Argentina Elo: 2151",
                ),
                ChainStep(
                    agent_id="simulation_agent",
                    action="monte_carlo",
                    result="10K runs: Argentina wins 55%",
                ),
            ],
            total_confidence=0.72,
        )
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    root_belief_id: str
    conclusion: str
    steps: list[dict] = field(default_factory=list)
    total_confidence: float = 0.0
    challenge_count: int = 0  # Number of times this belief was challenged

    def add_step(
        self,
        agent_id: str,
        action: str,
        result: Any,
        evidence_produced: list[Evidence] | None = None,
    ) -> None:
        """Add a step to the reasoning chain."""
        self.steps.append({
            "agent_id": agent_id,
            "action": action,
            "result": str(result),
            "evidence": [e.to_dict() if hasattr(e, 'to_dict') else e for e in (evidence_produced or [])],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "root_belief_id": self.root_belief_id,
            "conclusion": self.conclusion,
            "steps": self.steps,
            "total_confidence": round(self.total_confidence, 4),
            "challenge_count": self.challenge_count,
        }


@dataclass
class ConflictRecord:
    """
    Record of a conflict between agents or beliefs.

    This enables the debate mechanism.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # What conflicted
    belief_a_id: str
    belief_b_id: str

    # Agents involved
    agent_a: str
    agent_b: str

    # Details
    belief_a_value: Any
    belief_b_value: Any
    divergence: float  # How different are they?

    # Resolution
    is_resolved: bool = False
    resolution: str | None = None
    winner: str | None = None  # Which belief survived?

    # Discussion/辩论
    agent_a_argument: str = ""
    agent_b_argument: str = ""
    resolution_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "belief_a": {"id": self.belief_a_id, "value": self.belief_a_value, "agent": self.agent_a},
            "belief_b": {"id": self.belief_b_id, "value": self.belief_b_value, "agent": self.agent_b},
            "divergence": round(self.divergence, 4),
            "is_resolved": self.is_resolved,
            "resolution": self.resolution,
            "winner": self.winner,
            "agent_a_argument": self.agent_a_argument,
            "agent_b_argument": self.agent_b_argument,
            "resolution_reason": self.resolution_reason,
        }


# ── Cognitive World Model ────────────────────────────────────────────────────


class CognitiveWorldModel:
    """
    Cognitive World Model — the brain of the multi-agent system.

    Upgrades the simple WorldState into a proper belief model with:
      - Explicit beliefs with confidence scores
      - Evidence chains showing reasoning
      - Uncertainty quantification
      - Conflict detection and resolution

    This enables the system to answer:
      - "Why did you predict X?" → Trace evidence chains
      - "How confident are you?" → Check confidence scores
      - "What could change your mind?" → Identify uncertain beliefs
    """

    def __init__(self):
        self.beliefs: dict[str, Belief] = {}
        self.evidence_chains: dict[str, EvidenceChain] = {}
        self.conflicts: list[ConflictRecord] = []
        self._belief_index: dict[str, dict[str, str]] = {}  # subject -> predicate -> belief_id

    # ── Belief Management ──────────────────────────────────────────────────

    def assert_belief(
        self,
        subject: str,
        predicate: str,
        value: Any,
        confidence: float = 0.5,
        uncertainty: dict[str, float] | None = None,
        evidence: list[Evidence] | None = None,
        agent_id: str | None = None,
    ) -> Belief:
        """
        Assert a new belief into the model.

        This is the main way agents add knowledge to the system.
        """
        # Generate belief ID
        belief_id = f"{subject}:{predicate}"

        # Create belief
        belief = Belief(
            id=belief_id,
            subject=subject,
            predicate=predicate,
            value=value,
            confidence=confidence,
            uncertainty=uncertainty or {},
            evidence=evidence or [],
            agent_id=agent_id,
        )

        # Update confidence based on evidence
        belief.update_confidence()

        # Store
        self.beliefs[belief_id] = belief

        # Index for fast lookup
        if subject not in self._belief_index:
            self._belief_index[subject] = {}
        self._belief_index[subject][predicate] = belief_id

        return belief

    def get_belief(self, subject: str, predicate: str) -> Belief | None:
        """Get a belief by subject and predicate."""
        belief_id = f"{subject}:{predicate}"
        return self.beliefs.get(belief_id)

    def get_beliefs_about(self, subject: str) -> list[Belief]:
        """Get all beliefs about a subject."""
        if subject not in self._belief_index:
            return []
        return [
            self.beliefs[bid]
            for bid in self._belief_index[subject].values()
            if bid in self.beliefs
        ]

    def update_belief(
        self,
        subject: str,
        predicate: str,
        value: Any,
        agent_id: str,
        additional_evidence: list[Evidence] | None = None,
    ) -> tuple[Belief | None, bool]:
        """
        Update an existing belief with new evidence.

        Returns:
          - Updated belief or None if not found
          - Whether a conflict was detected
        """
        belief_id = f"{subject}:{predicate}"
        existing = self.beliefs.get(belief_id)

        if not existing:
            # Create new belief
            belief = self.assert_belief(
                subject=subject,
                predicate=predicate,
                value=value,
                agent_id=agent_id,
                evidence=additional_evidence,
            )
            return belief, False

        # Check for conflict
        conflict = self._detect_conflict(existing, value, agent_id)

        if conflict:
            self.conflicts.append(conflict)
            existing.is_contested = True
            return existing, True

        # Update existing belief
        old_confidence = existing.confidence
        existing.value = value
        existing.agent_id = agent_id
        existing.updated_at = datetime.now(timezone.utc).isoformat()

        if additional_evidence:
            for ev in additional_evidence:
                existing.add_evidence(ev)

        return existing, False

    def _detect_conflict(
        self,
        existing: Belief,
        new_value: Any,
        new_agent_id: str,
    ) -> ConflictRecord | None:
        """Detect if new value conflicts with existing belief."""
        if not isinstance(existing.value, (int, float)) or not isinstance(new_value, (int, float)):
            return None

        # Calculate divergence
        divergence = abs(existing.value - new_value)

        # Threshold for conflict (> 10% difference)
        if divergence < 0.10:
            return None

        return ConflictRecord(
            belief_a_id=existing.id,
            belief_b_id=f"{existing.subject}:{existing.predicate}:new",
            agent_a=existing.agent_id or "unknown",
            agent_b=new_agent_id,
            belief_a_value=existing.value,
            belief_b_value=new_value,
            divergence=divergence,
        )

    # ── Evidence Chain Management ─────────────────────────────────────────

    def create_evidence_chain(
        self,
        root_belief_id: str,
        conclusion: str,
    ) -> EvidenceChain:
        """Start a new evidence chain for a belief."""
        chain = EvidenceChain(
            root_belief_id=root_belief_id,
            conclusion=conclusion,
        )
        self.evidence_chains[chain.id] = chain
        return chain

    def extend_evidence_chain(
        self,
        chain_id: str,
        agent_id: str,
        action: str,
        result: Any,
        evidence_produced: list[Evidence] | None = None,
    ) -> None:
        """Add a step to an evidence chain."""
        chain = self.evidence_chains.get(chain_id)
        if chain:
            chain.add_step(agent_id, action, result, evidence_produced)

    # ── Conflict Resolution ────────────────────────────────────────────────

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        winner: str,
        reason: str,
    ) -> None:
        """Resolve a conflict between beliefs."""
        for conflict in self.conflicts:
            if conflict.id == conflict_id:
                conflict.is_resolved = True
                conflict.resolution = resolution
                conflict.winner = winner
                conflict.resolution_reason = reason

                # Update beliefs
                if winner == "a":
                    # Belief A wins, B is marked contested
                    belief_a = self.beliefs.get(conflict.belief_a_id)
                    if belief_a:
                        belief_a.is_verified = True
                elif winner == "b":
                    # Belief B wins, update A
                    belief_a = self.beliefs.get(conflict.belief_a_id)
                    if belief_a:
                        belief_a.value = conflict.belief_b_value
                        belief_a.is_contested = False
                        belief_a.is_verified = True

    # ── Query Methods ─────────────────────────────────────────────────────

    def get_uncertain_beliefs(self, threshold: float = 0.6) -> list[Belief]:
        """Get beliefs with low confidence (could be changed by new evidence)."""
        return [
            b for b in self.beliefs.values()
            if b.confidence < threshold
        ]

    def get_contested_beliefs(self) -> list[Belief]:
        """Get beliefs that have conflicts."""
        return [
            b for b in self.beliefs.values()
            if b.is_contested
        ]

    def get_unverified_beliefs(self) -> list[Belief]:
        """Get beliefs that haven't been cross-checked."""
        return [
            b for b in self.beliefs.values()
            if not b.is_verified and not b.is_contested
        ]

    def explain_belief(self, subject: str, predicate: str) -> dict | None:
        """
        Generate a full explanation for a belief.

        Returns evidence chain and reasoning.
        """
        belief = self.get_belief(subject, predicate)
        if not belief:
            return None

        # Find relevant evidence chain
        chain = None
        for c in self.evidence_chains.values():
            if c.root_belief_id == belief.id:
                chain = c
                break

        return {
            "belief": belief.to_dict(),
            "confidence_breakdown": {
                "total": belief.confidence,
                "evidence_count": len(belief.evidence),
                "evidence_weights": [
                    {
                        "source": e.source.value,
                        "contribution": e.confidence_contribution(),
                    }
                    for e in belief.evidence
                ],
            },
            "uncertainty": belief.uncertainty,
            "evidence_chain": chain.to_dict() if chain else None,
            "status": {
                "is_verified": belief.is_verified,
                "is_contested": belief.is_contested,
            },
        }

    # ── Serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "beliefs": {k: v.to_dict() for k, v in self.beliefs.items()},
            "evidence_chains": {k: v.to_dict() for k, v in self.evidence_chains.items()},
            "conflicts": [c.to_dict() for c in self.conflicts],
            "stats": {
                "total_beliefs": len(self.beliefs),
                "verified_beliefs": sum(1 for b in self.beliefs.values() if b.is_verified),
                "contested_beliefs": sum(1 for b in self.beliefs.values() if b.is_contested),
                "unresolved_conflicts": sum(1 for c in self.conflicts if not c.is_resolved),
                "avg_confidence": sum(b.confidence for b in self.beliefs.values()) / max(1, len(self.beliefs)),
            },
        }
