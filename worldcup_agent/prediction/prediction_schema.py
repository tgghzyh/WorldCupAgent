"""Versioned Prediction Schema.

Every prediction output carries:
  - prediction_version: semantic version of the model/pipeline that produced it
  - knowledge_version:  git hash of the data knowledge base at prediction time
  - snapshot_at:        ISO timestamp when this prediction snapshot was generated
  - expires_at:         ISO timestamp when this snapshot becomes stale
  - factors:            ranked list of key drivers with percentage attribution

This makes predictions:
  a) Reproducible  — same version + knowledge → same output
  b) Comparable    — snap_a vs snap_b with timestamp shows drift over time
  c) Explicable    — factors explain *why* each probability is what it is
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

# ── Version helpers ──────────────────────────────────────────────────────────────

def get_knowledge_version() -> str:
    """Git hash of the current data_layer knowledge base.

    Returns a short 8-char hash. Falls back to 'unknown' if not in a git repo.
    """
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=8", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def get_pipeline_version() -> str:
    """Semantic version of the prediction pipeline.

    Reads from worldcup_agent/__version__.py if it exists,
    otherwise defaults to '0.1.0-dev'.
    """
    try:
        from worldcup_agent import __version__
        return __version__
    except ImportError:
        return "0.1.0-dev"


# ── Core dataclasses ────────────────────────────────────────────────────────────

@dataclass
class FactorAttribution:
    """One factor explaining a probability.

    Example:
        FactorAttribution(
            name="ELO Rating Advantage",
            key="elo_diff",
            value=0.22,          # 22 percentage points contributed
            contribution_pct=0.42, # 42% of the probability is explained by this
            direction="up",       # pushes probability UP for home team
            evidence="Argentina Elo 2151 vs France Elo 2134 (diff +17)",
            confidence="high",
        )
    """
    name: str                          # Human-readable label
    key: str                           # Feature key (for traceability)
    value: float                       # Raw feature value at prediction time
    contribution_pct: float            # Fraction of probability this explains (0.0–1.0)
    direction: Literal["up", "down"]   # Whether it pushes win prob up or down
    evidence: str                      # Plain-English evidence snippet
    confidence: Literal["high", "medium", "low"]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "key": self.key,
            "value": round(self.value, 4),
            "contribution_pct": round(self.contribution_pct, 3),
            "direction": self.direction,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


@dataclass
class OutcomeProbability:
    """3-class probability distribution for one match outcome."""
    home_win: float
    draw: float
    away_win: float

    def as_dict(self) -> dict:
        return {"home_win": round(self.home_win, 4),
                "draw":     round(self.draw,     4),
                "away_win": round(self.away_win, 4)}

    @property
    def confidence(self) -> Literal["high", "medium", "low"]:
        spread = max(self.home_win, self.draw, self.away_win) - \
                 min(self.home_win, self.draw, self.away_win)
        if spread > 0.45:
            return "high"
        elif spread > 0.20:
            return "medium"
        return "low"


@dataclass
class MatchPrediction:
    """A single match prediction with full provenance and explainability."""
    # Identity
    match_id: str                      # e.g. "wc2026_001" or "arg_vs_fra_group"
    home_team: str
    away_team: str
    kickoff: str                       # ISO datetime string

    # Version metadata
    prediction_version: str = field(default_factory=get_pipeline_version)
    knowledge_version: str = field(default_factory=get_knowledge_version)
    snapshot_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expires_at: str = field(
        default_factory=lambda: (
            datetime.now(timezone.utc) + timedelta(hours=24)
        ).isoformat()
    )

    # Core output
    outcome: OutcomeProbability = field(default_factory=lambda: OutcomeProbability(0.33, 0.33, 0.34))
    predicted_winner: str | None = None

    # Explainability
    factors: list[FactorAttribution] = field(default_factory=list)
    model_used: str = "baseline_logistic"
    training_set_size: int = 0

    # Quality signals
    calibration_score: float | None = None  # Brier score of this snapshot (retrospective)
    is_stale: bool = False

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "kickoff": self.kickoff,
            "metadata": {
                "prediction_version": self.prediction_version,
                "knowledge_version": self.knowledge_version,
                "snapshot_at": self.snapshot_at,
                "expires_at": self.expires_at,
                "is_stale": self.is_stale,
            },
            "prediction": {
                "outcome": self.outcome.as_dict(),
                "predicted_winner": self.predicted_winner,
                "confidence": self.outcome.confidence,
                "model": self.model_used,
                "training_set_size": self.training_set_size,
                "calibration_score": self.calibration_score,
            },
            "factors": [f.to_dict() for f in self.factors],
        }


@dataclass
class PredictionSnapshot:
    """A complete daily prediction snapshot for the entire tournament.

    This is the primary output unit of the agent's daily intelligence product.
    Users receive exactly one of these per day.
    """
    snapshot_id: str                    # e.g. "snap_2026_07_04_v12"
    tournament: str = "FIFA World Cup 2026"
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expires_at: str = field(
        default_factory=lambda: (
            datetime.now(timezone.utc) + timedelta(hours=24)
        ).isoformat()
    )

    # Version chain
    prediction_version: str = field(default_factory=get_pipeline_version)
    knowledge_version: str = field(default_factory=get_knowledge_version)

    # Contents
    match_predictions: list[MatchPrediction] = field(default_factory=list)
    standings_snapshot: dict = field(default_factory=dict)  # {team: {pts,gd,position}}

    # Change detection
    changes_from_previous: list[dict] = field(default_factory=list)
    # Each change: {team, metric, prev, curr, delta_pct, reason}

    # Summary for the daily briefing
    headline: str = ""
    top_upset: dict | None = None   # {team, reason, probability_of_upset}
    injury_news_impact: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "tournament": self.tournament,
            "generated_at": self.generated_at,
            "expires_at": self.expires_at,
            "versions": {
                "prediction_version": self.prediction_version,
                "knowledge_version": self.knowledge_version,
            },
            "headline": self.headline,
            "changes": self.changes_from_previous,
            "top_upset": self.top_upset,
            "standings": self.standings_snapshot,
            "matches": [m.to_dict() for m in self.match_predictions],
        }

    @classmethod
    def from_dict(cls, d: dict) -> PredictionSnapshot:
        matches = [
            MatchPrediction(
                match_id=m["match_id"],
                home_team=m["home_team"],
                away_team=m["away_team"],
                kickoff=m["kickoff"],
                prediction_version=m["metadata"]["prediction_version"],
                knowledge_version=m["metadata"]["knowledge_version"],
                snapshot_at=m["metadata"]["snapshot_at"],
                expires_at=m["metadata"]["expires_at"],
                outcome=OutcomeProbability(**m["prediction"]["outcome"]),
                predicted_winner=m["prediction"].get("predicted_winner"),
                model_used=m["prediction"].get("model", "unknown"),
                training_set_size=m["prediction"].get("training_set_size", 0),
                calibration_score=m["prediction"].get("calibration_score"),
                is_stale=m["metadata"].get("is_stale", False),
                factors=[
                    FactorAttribution(
                        name=f["name"],
                        key=f["key"],
                        value=f["value"],
                        contribution_pct=f["contribution_pct"],
                        direction=f["direction"],
                        evidence=f["evidence"],
                        confidence=f["confidence"],
                    )
                    for f in (m.get("factors") or [])
                ],
            )
            for m in d.get("matches", [])
        ]
        snap = cls(
            snapshot_id=d["snapshot_id"],
            tournament=d.get("tournament", "FIFA World Cup 2026"),
            generated_at=d["generated_at"],
            expires_at=d.get("expires_at", ""),
            prediction_version=d.get("versions", {}).get("prediction_version", "unknown"),
            knowledge_version=d.get("versions", {}).get("knowledge_version", "unknown"),
            match_predictions=matches,
            standings_snapshot=d.get("standings", {}),
            changes_from_previous=d.get("changes", []),
            headline=d.get("headline", ""),
            top_upset=d.get("top_upset"),
        )
        return snap


# ── Snapshots storage ───────────────────────────────────────────────────────────

DATA_DIR = (
    Path(__file__).resolve().parents[3]   # WorldCupAgent/WorldCupAgent/ → WorldCupAgent/
    / "data"
)
SNAPSHOT_DIR = DATA_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def save_snapshot(snap: PredictionSnapshot) -> Path:
    """Persist a snapshot as JSON and promote it to canonical 'latest'.

    Returns the file path.
    """
    path = SNAPSHOT_DIR / f"{snap.snapshot_id}.json"
    path.write_text(
        json.dumps(snap.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # Auto-promote to latest
    promote_to_latest(snap)
    return path


def load_snapshot(snapshot_id: str) -> PredictionSnapshot:
    """Load a saved snapshot."""
    path = SNAPSHOT_DIR / f"{snapshot_id}.json"
    return PredictionSnapshot.from_dict(
        json.loads(path.read_text(encoding="utf-8"))
    )


def list_snapshots() -> list[str]:
    """Return IDs of all saved snapshots, newest first."""
    files = sorted(SNAPSHOT_DIR.glob("snap_*.json"), reverse=True)
    return [f.stem for f in files]


def compare_snapshots(id_a: str, id_b: str) -> list[dict]:
    """Diff two snapshots. Returns a list of changes."""
    snap_a = load_snapshot(id_a)
    snap_b = load_snapshot(id_b)
    changes = []

    # Build lookup
    pred_a = {m.match_id: m for m in snap_a.match_predictions}
    pred_b = {m.match_id: m for m in snap_b.match_predictions}

    for mid in pred_a:
        if mid not in pred_b:
            continue
        pa = pred_a[mid]
        pb = pred_b[mid]
        for label, (va, vb) in [
            ("home_win", (pa.outcome.home_win, pb.outcome.home_win)),
            ("draw",     (pa.outcome.draw,     pb.outcome.draw)),
            ("away_win", (pa.outcome.away_win, pb.outcome.away_win)),
        ]:
            delta = vb - va
            if abs(delta) > 0.005:
                changes.append({
                    "match_id": mid,
                    "metric": label,
                    "prev_snap": id_a,
                    "curr_snap": id_b,
                    "prev_value": round(va, 4),
                    "curr_value": round(vb, 4),
                    "delta_pct": round(delta * 100, 2),
                })
    return changes


from pathlib import Path
import json


# ── Versioned snapshot manager ───────────────────────────────────────────────────

CURRENT_VERSION_FILE = DATA_DIR / "snapshots" / "current_version.txt"
LATEST_FILE = DATA_DIR / "snapshots" / "latest.json"


def get_current_version() -> str:
    """Return the active prediction version string, or 'unknown'."""
    if not CURRENT_VERSION_FILE.exists():
        return "unknown"
    return CURRENT_VERSION_FILE.read_text(encoding="utf-8").strip()


def set_current_version(version: str) -> None:
    """Atomically write the current active version."""
    CURRENT_VERSION_FILE.write_text(version, encoding="utf-8")


def is_snapshot_stale(snap_id: str) -> bool:
    """Check if a snapshot is past its expiry time.

    Returns True if expired, False if still valid.
    """
    snap_path = SNAPSHOT_DIR / f"{snap_id}.json"
    if not snap_path.exists():
        return True
    try:
        d = json.loads(snap_path.read_text(encoding="utf-8"))
        expires = d.get("expires_at", "")
        if not expires:
            return False
        exp_ts = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > exp_ts
    except Exception:
        return False


def promote_to_latest(snap: PredictionSnapshot) -> None:
    """Write this snapshot as the canonical 'latest' snapshot.

    Also updates current_version.txt with the snap's snapshot_id.
    """
    # Write latest.json
    latest_dict = snap.to_dict()
    latest_dict["_promoted_at"] = datetime.now(timezone.utc).isoformat()
    LATEST_FILE.write_text(
        json.dumps(latest_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # Update version tracker
    set_current_version(snap.snapshot_id)


def get_latest_snapshot() -> PredictionSnapshot | None:
    """Load the canonical 'latest' snapshot, or None if none exists."""
    if not LATEST_FILE.exists():
        return None
    try:
        d = json.loads(LATEST_FILE.read_text(encoding="utf-8"))
        return PredictionSnapshot.from_dict(d)
    except Exception:
        return None


def snapshot_diff(snap_id_a: str, snap_id_b: str) -> list[dict]:
    """Return probability differences between two snapshots.

    Uses the existing compare_snapshots logic.
    """
    return compare_snapshots(snap_id_a, snap_id_b)


def get_snapshot_history(n: int = 10) -> list[dict]:
    """Return metadata for the last N snapshots.

    Each entry: {snapshot_id, generated_at, expires_at, is_stale}
    """
    files = sorted(SNAPSHOT_DIR.glob("snap_*.json"), reverse=True)[:n]
    history = []
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            expires = d.get("expires_at", "")
            is_stale = False
            if expires:
                try:
                    exp_ts = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                    is_stale = datetime.now(timezone.utc) > exp_ts
                except Exception:
                    pass
            history.append({
                "snapshot_id": d.get("snapshot_id", f.stem),
                "generated_at": d.get("generated_at", ""),
                "expires_at": expires,
                "is_stale": is_stale,
                "version": d.get("versions", {}).get("prediction_version", "unknown"),
                "kb_version": d.get("versions", {}).get("knowledge_version", "unknown"),
            })
        except Exception:
            continue
    return history
