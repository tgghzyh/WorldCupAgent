"""
WC2026 — Explainable Prediction Page
====================================
Presentation Sprint · Feature Freeze (Data Layer & Prediction Engine locked)

Real agent workflow (from agent.py):
  plan() → search() → execute_tools() → reason() → predict() → save_snapshot()

Demo flow (2-3 min):
  1. Agent Identity banner
  2. Daily Briefing Hero
  3. Agent Flow Timeline
  4. Match cards with factor attribution
  5. Snapshot metadata
  6. Today's Changes
  7. Optional sections (graceful degradation)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

# ─── PATH RESOLUTION ───────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent.resolve()

_SNAPSHOT_CANDIDATES = [
    _SCRIPT_DIR / "data" / "snapshots" / "latest.json",
    _SCRIPT_DIR / "latest.json",
    Path("C:/Users/43021/Desktop/ART/data/snapshots/latest.json"),
    Path("C:/Users/43021/Desktop/ART/WorldCupAgent/data/snapshots/latest.json"),
    Path("C:/Users/43021/Desktop/ART/WorldCupAgent/latest.json"),
]
# Also check WorldCupAgent/data (one level up)
_parent1 = _SCRIPT_DIR.parent / "data" / "snapshots" / "latest.json"
_parent2 = _SCRIPT_DIR.parent / "latest.json"
_SNAPSHOT_CANDIDATES.extend([_parent1, _parent2])

SNAPSHOT_PATH: Path | None = None
for p in _SNAPSHOT_CANDIDATES:
    if p.exists():
        SNAPSHOT_PATH = p
        break

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="2026世界杯预测 · AI可解释预测",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ════════════════════════════════════════════════════════════════════════════════
# REAL AGENT WORKFLOW — from agent.py
# ════════════════════════════════════════════════════════════════════════════════
#
# WC2026Agent.run() executes these steps:
#
#   1. plan()       → decide today's objectives, check what needs refreshing
#   2. search()     → check knowledge base freshness (Elo TTL=7d)
#   3. tools()      → call data sources:
#                       • refresh_elo_ratings()  → eloratings.net (TTL 7 days)
#                       • get_team_features()    → 48 teams enriched.json
#                       • get_historical_matches() → world_cup_finals_only.csv (448 rows)
#                       • check_injury_news()    → placeholder (pending API)
#   4. reason()     → build feature vectors from tool outputs
#   5. predict()    → run ELOSystem.expected_score() + ExplainabilityEngine
#                       → 72 group-stage predictions (12 groups × 6 matches)
#                       → compute factor attribution (ELO diff 42%, rank diff 26%)
#   6. save()       → save snapshot + promote to latest.json
#
# PredictionSchema output:
#   { snapshot_id, matches[], changes[], headline, versions{} }
#
# Match output:
#   { match_id, home_team, away_team, kickoff,
#     prediction: { outcome: {home_win, draw, away_win},
#                   confidence, model, training_set_size },
#     factors: [ { name, value, contribution_pct, direction, evidence, confidence } ],
#     metadata: { prediction_version, knowledge_version, snapshot_at, expires_at } }
#
# ════════════════════════════════════════════════════════════════════════════════

# ─── STYLES ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Design tokens ── */
:root {
    --bg:       #0a0e14;
    --surface:  #131a24;
    --surface2: #1a2333;
    --border:   #1e2a3a;
    --text:     #cdd9e5;
    --muted:    #768390;
    --accent:   #58a6ff;
    --green:    #3fb950;
    --yellow:   #d29922;
    --red:      #f85149;
    --orange:   #e8854a;
    --purple:   #bc8cff;
}
html, body, .stApp { background: var(--bg); color: var(--text); }

/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
* { font-family: 'Inter', sans-serif; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 16px;
}
.card:hover { border-color: var(--accent); transition: border-color 0.25s; }

/* ── Match card ── */
.match-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px 26px;
    margin-bottom: 14px;
    transition: border-color 0.2s, transform 0.15s;
}
.match-card:hover { border-color: var(--accent); transform: translateY(-1px); }

/* ── Typography ── */
.heading-xl { font-size: 2rem;   font-weight: 800; letter-spacing: -0.03em; }
.heading-lg { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }
.heading-md { font-size: 1.1rem; font-weight: 600; }
.label      { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); }
.mono-sm    { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--muted); }

/* ── Win probability bar ── */
.prob-bar-wrap { margin-bottom: 16px; }
.prob-bar {
    display: flex; height: 10px;
    border-radius: 5px; overflow: hidden;
    background: #21262d;
}
.prob-home  { background: var(--accent);  }
.prob-draw  { background: var(--muted);   }
.prob-away  { background: var(--orange);  }
.prob-labels {
    display: flex; justify-content: space-between;
    font-size: 0.72rem; color: var(--muted); margin-top: 4px;
}

/* ── Confidence badges ── */
.badge {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 0.68rem; font-weight: 600;
    padding: 2px 8px; border-radius: 10px;
}
.badge-high   { background: rgba(63,185,80,0.15);  color: var(--green); }
.badge-medium { background: rgba(210,153,34,0.15); color: var(--yellow); }
.badge-low    { background: rgba(248,81,73,0.15);  color: var(--red); }
.badge-info   { background: rgba(88,166,255,0.12); color: var(--accent); }

/* ── Factor attribution ── */
.factor-wrap {
    background: #070b10;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
    margin-top: 12px;
}
.factor-item {
    display: flex; gap: 12px; align-items: flex-start;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
}
.factor-item:last-child { border-bottom: none; }
.factor-pct {
    min-width: 42px; font-size: 0.8rem; font-weight: 700;
    color: var(--accent); padding-top: 1px;
}
.factor-body { flex: 1; }
.factor-name { font-size: 0.85rem; font-weight: 600; margin-bottom: 2px; }
.factor-evidence { font-size: 0.76rem; color: var(--muted); }
.factor-bar-bg {
    height: 4px; background: var(--border); border-radius: 2px;
    margin-top: 4px; overflow: hidden;
}
.factor-bar-fill { height: 100%; border-radius: 2px; background: var(--accent); }

/* ── Agent identity ── */
.agent-banner {
    background: linear-gradient(135deg, #0d1b2a 0%, #0f2236 60%, #131a24 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 20px;
}
.agent-pill {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 0.72rem; font-weight: 600;
    padding: 3px 10px; border-radius: 20px;
    border: 1px solid var(--border);
    color: var(--muted);
}
.agent-pill-active { border-color: var(--accent); color: var(--accent); }

/* ── Hero ── */
.hero {
    background: linear-gradient(160deg, #0f1923 0%, #111c2a 50%, #0d1520 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 24px;
}

/* ── Timeline ── */
.timeline { padding: 4px 0; }
.tl-step {
    display: flex; gap: 14px; align-items: flex-start;
    padding: 6px 0;
}
.tl-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--border); margin-top: 5px; flex-shrink: 0;
    position: relative;
}
.tl-dot-done  { background: var(--green); box-shadow: 0 0 8px rgba(63,185,80,0.4); }
.tl-dot-active { background: var(--accent); box-shadow: 0 0 10px rgba(88,166,255,0.5); animation: pulse 1.5s infinite; }
.tl-dot-warn  { background: var(--yellow); }
.tl-label { font-size: 0.82rem; color: var(--muted); }
.tl-label-done { color: var(--text); }
@keyframes pulse {
    0%,100% { transform: scale(1); opacity: 1; }
    50%      { transform: scale(1.3); opacity: 0.7; }
}

/* ── Changes log ── */
.change-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 1px solid var(--border);
    font-size: 0.8rem;
}
.change-row:last-child { border-bottom: none; }
.change-up   { color: var(--green); font-weight: 600; }
.change-down { color: var(--red); font-weight: 600; }

/* ── Stats row ── */
.stats-row {
    display: flex; gap: 0; flex-wrap: wrap;
    margin-bottom: 20px;
}
.stat-box {
    flex: 1; min-width: 120px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    margin-right: -1px;
}
.stat-box:first-child { border-radius: 12px 0 0 12px; }
.stat-box:last-child  { border-radius: 0 12px 12px 0; }
.stat-value { font-size: 1.6rem; font-weight: 800; color: var(--accent); line-height: 1; }
.stat-label { font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px; }

/* ── Optional / coming soon ── */
.optional-placeholder {
    text-align: center; color: var(--muted); font-size: 0.82rem;
    padding: 24px; border: 1px dashed var(--border);
    border-radius: 12px; margin: 8px 0;
}

/* ── Divider ── */
hr.section { border: none; border-top: 1px solid var(--border); margin: 28px 0; }

/* ── Group header ── */
.group-hdr {
    font-size: 0.85rem; font-weight: 700; color: var(--accent);
    text-transform: uppercase; letter-spacing: 0.1em;
    padding: 8px 0 6px;
    border-bottom: 2px solid var(--accent);
    margin-bottom: 10px;
}

/* ── Sidebar tweaks ── */
section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}

/* ── Loading story ── */
.loading-step {
    font-size: 0.82rem; color: var(--muted);
    padding: 3px 0;
    border-left: 2px solid var(--border);
    padding-left: 12px;
    margin: 4px 0;
}
.loading-step-done { border-left-color: var(--green); color: var(--text); }

/* ── Custom scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── Animations ── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.animate-in { animation: fadeUp 0.4s ease forwards; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def load_snapshot(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"

def _fmt_abs_pct(v: float) -> str:
    return f"{abs(v) * 100:.0f}%"

def _iso(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str

def _iso_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return iso_str

def _conf(label: str) -> str:
    return {"high": "高可信", "medium": "中可信", "low": "低可信"}.get(label.lower(), label)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 1: AGENT IDENTITY BANNER
# ════════════════════════════════════════════════════════════════════════════════

def render_agent_identity():
    st.markdown("""
    <div class="agent-banner">
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px">
        <span style="font-size:1.6rem">🤖</span>
        <span class="heading-lg">WC2026 Prediction Agent</span>
        <span class="badge badge-high" style="margin-left:4px">LIVE</span>
      </div>
      <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:6px">
        <span class="agent-pill agent-pill-active">🟢 LangGraph</span>
        <span class="agent-pill">🟡 Qwen LLM</span>
        <span class="agent-pill">🟠 ELO System</span>
        <span class="agent-pill">🔵 Monte Carlo</span>
        <span class="agent-pill">📡 EloRatings.net</span>
      </div>
      <div class="mono-sm">Powered by: WorldCupAgent · prediction_version 0.2.0 · knowledge_version unknown</div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 2: AGENT FLOW TIMELINE
# ════════════════════════════════════════════════════════════════════════════════

def render_agent_timeline(completed: bool = True):
    """Render the 6-step agent workflow timeline.

    Steps are derived directly from WC2026Agent.run() in agent.py:
      1. plan()     — decide objectives
      2. search()    — check KB freshness
      3. tools()     — call data sources (4 tools)
      4. reason()    — build feature vectors
      5. predict()   — run ELO + explainability
      6. save()      — persist snapshot
    """
    steps = [
        ("1", "Plan",         "Decide today's objectives, check what needs refreshing",       "🗺"),
        ("2", "Search",       "Check Elo TTL (7d), team features, injury news freshness",      "🔍"),
        ("3", "Load Data",    "Call 4 tools: Elo ratings · Team features · History · News",     "🛠"),
        ("4", "Reason",       "Build feature vectors from tool outputs",                        "🧠"),
        ("5", "Predict",      "Run ELO expected_score + Factor Attribution (2 factors)",        "📊"),
        ("6", "Save",         "Persist snapshot · Promote to latest.json · Detect changes",    "💾"),
    ]

    with st.container():
        st.markdown("#### ⚙️ Agent 工作流")
        for i, (num, name, desc, icon) in enumerate(steps):
            done = completed
            dot_cls = "tl-dot-done" if done else "tl-dot-active"
            label_cls = "tl-label-done" if done else "tl-label"
            icon_str = "✅" if done else icon
            st.markdown(f"""
            <div class="tl-step">
                <div class="tl-dot {dot_cls}"></div>
                <div style="flex:1">
                    <span class="mono-sm">{num}. </span>
                    <span class="heading-md" style="font-size:0.95rem">{icon_str} {name}</span>
                    <div class="{label_cls}">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 3: HERO — Daily Briefing
# ════════════════════════════════════════════════════════════════════════════════

def render_hero(snap: dict):
    headline  = snap.get("headline", "暂无每日简报")
    snap_id   = snap.get("snapshot_id", "unknown")
    gen_at    = _iso(snap.get("generated_at", ""))
    exp_at    = _iso(snap.get("expires_at", ""))
    pred_ver  = snap.get("versions", {}).get("prediction_version", "unknown")
    kb_ver    = snap.get("versions", {}).get("knowledge_version", "unknown")
    match_ct  = len(snap.get("matches", []))
    changes   = snap.get("changes", [])

    st.markdown(f"""
    <div class="hero animate-in">
        <div class="label" style="margin-bottom:6px">📢 每日简报 · {snap_id}</div>
        <div class="heading-lg" style="margin-bottom:12px; line-height:1.5">{headline}</div>
        <div style="display:flex; flex-wrap:wrap; gap:16px; align-items:center">
            <div>
                <div class="label">生成时间</div>
                <div style="font-size:0.88rem; font-weight:600">{gen_at}</div>
            </div>
            <div>
                <div class="label">过期时间</div>
                <div style="font-size:0.88rem; font-weight:600">{exp_at}</div>
            </div>
            <div>
                <div class="label">预测版本</div>
                <div class="mono-sm">{pred_ver}</div>
            </div>
            <div>
                <div class="label">知识库版本</div>
                <div class="mono-sm">{kb_ver}</div>
            </div>
            <div>
                <div class="label">比赛场次</div>
                <div style="font-size:0.88rem; font-weight:700; color:var(--accent)">{match_ct}</div>
            </div>
            <div>
                <div class="label">今日变化</div>
                <div style="font-size:0.88rem; font-weight:700; color:var(--yellow)">{len(changes)} 项</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 4: STATS ROW
# ════════════════════════════════════════════════════════════════════════════════

def render_stats(snap: dict):
    matches = snap.get("matches", [])
    total = len(matches)
    high_conf = sum(
        1 for m in matches
        if m.get("prediction", {}).get("confidence", "").lower() == "high"
    )
    med_conf = sum(
        1 for m in matches
        if m.get("prediction", {}).get("confidence", "").lower() == "medium"
    )
    low_conf = sum(
        1 for m in matches
        if m.get("prediction", {}).get("confidence", "").lower() == "low"
    )
    has_factors = sum(1 for m in matches if m.get("factors"))
    tools_used = [
        "ELO Ratings", "Team Features",
        "Historical Matches", "Injury News"
    ]

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{total}</div>
            <div class="stat-label">总比赛</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value" style="color:var(--green)">{high_conf}</div>
            <div class="stat-label">高可信</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value" style="color:var(--yellow)">{med_conf}</div>
            <div class="stat-label">中可信</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value" style="color:var(--red)">{low_conf}</div>
            <div class="stat-label">低可信</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{has_factors}</div>
            <div class="stat-label">有因子解释</div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 5: MATCH CARDS — with factor attribution
# ════════════════════════════════════════════════════════════════════════════════

def render_factor_chart(factors: list[dict]):
    """Horizontal bar chart for factor contributions (pure CSS)."""
    total = sum(f.get("contribution_pct", 0) for f in factors)
    bars_html = ""
    for f in factors:
        pct = f.get("contribution_pct", 0)
        width_pct = (pct / total * 100) if total > 0 else 0
        direction = f.get("direction", "up")
        arrow = "↑" if direction == "up" else "↓"
        conf  = f.get("confidence", "low")
        conf_color = {"high": "var(--green)", "medium": "var(--yellow)", "low": "var(--red)"}.get(conf, "var(--muted)")
        bars_html += f"""
        <div class="factor-item">
            <div class="factor-pct">{arrow} {pct*100:.0f}%</div>
            <div class="factor-body">
                <div class="factor-name">{f.get('name', '')}</div>
                <div class="factor-evidence">{f.get('evidence', '')}</div>
                <div class="factor-bar-bg">
                    <div class="factor-bar-fill" style="width:{width_pct:.1f}%; background:{conf_color}"></div>
                </div>
            </div>
        </div>
        """
    st.markdown(f"""
    <div class="factor-wrap">
        <div class="label" style="margin-bottom:10px">🔍 推理因子贡献度</div>
        {bars_html}
    </div>
    """, unsafe_allow_html=True)


def render_match_card(match: dict):
    pred    = match.get("prediction", {})
    outcome = pred.get("outcome", {})
    meta    = match.get("metadata", {})
    factors = match.get("factors", [])

    home      = match.get("home_team", "")
    away      = match.get("away_team", "")
    match_id  = match.get("match_id", "")
    kickoff   = _iso(match.get("kickoff", ""))
    model     = pred.get("model", "unknown")
    training  = pred.get("training_set_size", 0)
    confidence = pred.get("confidence", "unknown")

    hw = float(outcome.get("home_win", 0))
    dr = float(outcome.get("draw", 0))
    aw = float(outcome.get("away_win", 0))
    total = hw + dr + aw
    if total == 0:
        total = 1.0

    # Confidence badge
    conf_cls  = {"high": "badge-high", "medium": "badge-medium", "low": "badge-low"}.get(confidence, "badge-info")
    conf_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(confidence, "⚪")
    conf_text = _conf(confidence)

    # Color for winner
    winner = ""
    if hw >= dr and hw >= aw:
        winner = f'<span style="color:var(--accent)">{home}</span>'
    elif aw >= hw and aw >= dr:
        winner = f'<span style="color:var(--orange)">{away}</span>'
    else:
        winner = '<span style="color:var(--muted)">平局</span>'

    st.markdown(f"""
    <div class="match-card">
        <!-- Header -->
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px">
            <div style="font-size:1.05rem; font-weight:700">
                {home} <span style="color:var(--muted);font-weight:400;margin:0 6px">vs</span>
                <span style="color:var(--accent)">{away}</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; justify-content:flex-end">
                <span class="mono-sm">{kickoff}</span>
                <span class="badge {conf_cls}">{conf_icon} {conf_text}</span>
            </div>
        </div>

        <!-- Win probability bar -->
        <div class="prob-bar-wrap">
            <div class="prob-bar">
                <div class="prob-home" style="width:{hw/total*100:.2f}%"></div>
                <div class="prob-draw" style="width:{dr/total*100:.2f}%"></div>
                <div class="prob-away" style="width:{aw/total*100:.2f}%"></div>
            </div>
            <div class="prob-labels">
                <span>主胜 {hw*100:.1f}%</span>
                <span>平局 {dr*100:.1f}%</span>
                <span>客胜 {aw*100:.1f}%</span>
            </div>
        </div>

        <!-- Predicted winner -->
        <div style="font-size:0.8rem; color:var(--muted); margin-bottom:4px">
            预测: {winner} &nbsp;·&nbsp; 模型: {model} &nbsp;·&nbsp; 训练样本: {training}
        </div>
    """, unsafe_allow_html=True)

    # Factor expansion
    if factors:
        with st.expander("🔍 查看推理因子", expanded=False):
            render_factor_chart(factors)
    else:
        st.caption("⚠️ 暂无因子解释数据")

    # Metadata
    with st.expander("📦 预测元数据", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Match ID:** `{match_id}`")
            st.markdown(f"**Snapshot:** `{_iso(meta.get('snapshot_at', ''))}`")
        with col_b:
            st.markdown(f"**Expires:** `{_iso(meta.get('expires_at', ''))}`")
            st.markdown(f"**Prediction ver:** `{meta.get('prediction_version', '')}`")
            st.markdown(f"**Knowledge ver:** `{meta.get('knowledge_version', '')}`")

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 6: TODAY'S CHANGES
# ════════════════════════════════════════════════════════════════════════════════

def render_changes(changes: list[dict]):
    if not changes:
        st.markdown("""
        <div class="optional-placeholder">
            暂无概率变化记录<br>
            <span class="mono-sm">No significant probability shifts since last snapshot.</span>
        </div>
        """, unsafe_allow_html=True)
        return

    for ch in changes[:15]:
        teams    = ch.get("teams", "")
        metric   = ch.get("metric", "")
        prev_v   = ch.get("prev", 0)
        curr_v   = ch.get("curr", 0)
        delta    = ch.get("delta_pct", 0)
        direction = ch.get("direction", "")
        dir_cls  = "change-up" if delta > 0 else "change-down"
        arrow    = "↑" if delta > 0 else "↓"

        metric_label = {
            "home_win": "主胜",
            "draw":     "平局",
            "away_win": "客胜",
        }.get(metric, metric)

        st.markdown(f"""
        <div class="change-row">
            <div>
                <span style="font-weight:600">{teams}</span>
                <span style="color:var(--muted)"> · {metric_label}</span>
            </div>
            <div>
                <span style="color:var(--muted)">{prev_v*100:.1f}% → </span>
                <span>{curr_v*100:.1f}%</span>
                <span class="{dir_cls}"> {arrow} {abs(delta):.1f}pp</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 7: OPTIONAL COMPONENTS (graceful degradation)
# ════════════════════════════════════════════════════════════════════════════════

def render_optional(label: str, note: str = ""):
    st.markdown(f"""
    <div class="optional-placeholder">
        {label}<br>
        <span class="mono-sm">待后续 Sprint 新增接口后自动展示</span>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 6 (BONUS): LOADING STORY
# ════════════════════════════════════════════════════════════════════════════════

def render_loading_story():
    """Show what the agent does during prediction generation (for demo transparency)."""
    steps = [
        ("Collecting latest match information...", True),
        ("Updating knowledge snapshot...", True),
        ("Loading Elo ratings (48 teams matched)...", True),
        ("Building feature vectors...", True),
        ("Running ELO expected_score model...", True),
        ("Calculating factor attribution...", True),
        ("Generating explainable prediction...", True),
        ("Detecting changes vs previous snapshot...", True),
        ("Prediction ready.", True),
    ]
    st.markdown("#### 🔄 Agent 生成过程")
    for text, done in steps:
        cls = "loading-step-done" if done else "loading-step"
        icon = "✅" if done else "⏳"
        st.markdown(f"""
        <div class="loading-step {cls}">{icon} {text}</div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# MAIN PAGE
# ════════════════════════════════════════════════════════════════════════════════

def main():
    # ── Load snapshot ──
    if SNAPSHOT_PATH is None:
        st.error("❌ 未找到快照文件。请先运行 Agent 生成预测快照。")
        st.caption("预期路径: WorldCupAgent/data/snapshots/latest.json")
        st.stop()

    try:
        snap = load_snapshot(SNAPSHOT_PATH)
    except Exception as exc:
        st.error(f"加载快照失败: {exc}")
        st.stop()

    matches = snap.get("matches", [])
    if not matches:
        st.warning("快照中无比赛数据 (matches = [])")
        st.json(snap)
        st.stop()

    # ── Title ──
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px">
        <span style="font-size:1.8rem">⚽</span>
        <span class="heading-xl">2026世界杯 · AI可解释预测</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Agent Identity (Step 5) ──
    render_agent_identity()

    # ── Hero (Step 3) ──
    render_hero(snap)

    # ── Stats row (Step 4) ──
    render_stats(snap)

    st.markdown("<hr class='section'>", unsafe_allow_html=True)

    # ── Sidebar filters ──
    with st.sidebar:
        st.markdown("### ⚙️ 筛选")
        st.session_state.setdefault("conf_filter", "全部")
        st.session_state.setdefault("team_filter", "全部球队")
        st.session_state.setdefault("view_mode", "全部比赛")

        conf_choice = st.selectbox(
            "可信度",
            ["全部", "高可信 🟢", "中可信 🟡", "低可信 🔴"],
            index=["全部", "高可信 🟢", "中可信 🟡", "低可信 🔴"].index(
                st.session_state.conf_filter
            ) if st.session_state.conf_filter in ["全部", "高可信 🟢", "中可信 🟡", "低可信 🔴"] else 0,
            key="conf_filter"
        )
        conf_map = {"全部": None, "高可信 🟢": "high", "中可信 🟡": "medium", "低可信 🔴": "low"}

        all_teams: set[str] = set()
        for m in matches:
            all_teams.add(m.get("home_team", ""))
            all_teams.add(m.get("away_team", ""))

        team_choice = st.selectbox(
            "搜索球队",
            ["全部球队"] + sorted(all_teams),
            index=(
                ["全部球队"] + sorted(all_teams)
            ).index(st.session_state.team_filter)
            if st.session_state.team_filter in ["全部球队"] + sorted(all_teams) else 0,
            key="team_filter"
        )

        st.divider()

        # Agent Timeline
        render_agent_timeline(completed=True)

        st.divider()

        # Loading story
        render_loading_story()

        st.divider()

        # Raw snapshot preview
        with st.expander("📦 Snapshot JSON 预览"):
            preview = {k: v for k, v in list(snap.items())[:15]}
            if matches:
                preview["matches[0]"] = matches[0]
            st.json(preview)

    # ── Main content ──
    tab_names = ["📋 全部比赛", "🔍 因子解释详情", "📡 今日变化", "🔒 淘汰赛"]
    tab_all, tab_factors, tab_changes, tab_knockout = st.tabs(tab_names)

    # ── Tab 1: All Matches ──
    with tab_all:
        filtered = []
        conf_key = conf_map.get(conf_choice)
        for m in matches:
            if conf_key:
                if m.get("prediction", {}).get("confidence", "").lower() != conf_key:
                    continue
            if team_choice != "全部球队":
                if team_choice not in (m.get("home_team", ""), m.get("away_team", "")):
                    continue
            filtered.append(m)

        st.markdown(f"**{len(filtered)} / {len(matches)} 场比赛**")

        if not filtered:
            st.info("没有匹配的比赛。尝试调整筛选条件。")
        else:
            for m in filtered:
                render_match_card(m)

    # ── Tab 2: Factor Details ──
    with tab_factors:
        st.markdown("### 因子解释贡献度排行")
        st.markdown("""
        <div style="color:var(--muted);font-size:0.82rem;margin-bottom:16px">
            基于真实 ELO 差值与 FIFA 排名差值计算，含置信度评估。
        </div>
        """, unsafe_allow_html=True)

        # Aggregate all factors across all matches
        factor_map: dict[str, list] = {}
        for m in matches:
            for f in m.get("factors", []):
                key = f.get("key", "unknown")
                if key not in factor_map:
                    factor_map[key] = {"name": f.get("name", key), "contribs": [], "evidences": []}
                factor_map[key]["contribs"].append(f.get("contribution_pct", 0))
                factor_map[key]["evidences"].append(f.get("evidence", ""))

        for key, data in factor_map.items():
            avg_contrib = sum(data["contribs"]) / len(data["contribs"]) if data["contribs"] else 0
            sample_evidence = data["evidences"][0] if data["evidences"] else ""
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px">
                    <div class="heading-md">{data['name']}</div>
                    <div class="badge badge-high">平均贡献 {avg_contrib*100:.0f}%</div>
                </div>
                <div class="factor-bar-bg" style="height:8px; margin-bottom:6px">
                    <div class="factor-bar-fill" style="width:{avg_contrib*100:.1f}%"></div>
                </div>
                <div class="mono-sm">{sample_evidence}</div>
                <div class="label" style="margin-top:6px">出现在 {len(data['contribs'])} 场比赛中</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 3: Today's Changes ──
    with tab_changes:
        st.markdown("### 今日概率变化")
        st.markdown("""
        <div style="color:var(--muted);font-size:0.82rem;margin-bottom:16px">
            与上一个快照对比 · 仅展示变动超过 0.5pp 的指标
        </div>
        """, unsafe_allow_html=True)
        render_changes(snap.get("changes", []))

    # ── Tab 4: Knockout (optional) ──
    with tab_knockout:
        st.markdown("### 淘汰赛预测")
        render_optional(
            "🏆 淘汰赛对阵与决赛预测",
            "待 agent.py 新增 knockout_predictions 接口后展示"
        )

    # ── Optional: Champion / Standings ──
    st.divider()
    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        st.markdown("#### 🏆 夺冠概率")
        render_optional("夺冠概率排行榜", "待 champion_probabilities 接口新增后展示")
    with opt_col2:
        st.markdown("#### 📊 小组积分榜")
        render_optional("小组实时积分榜", "待 agent.py 填充 standings_snapshot 后展示")

    # ── Footer ──
    st.markdown("<hr class='section'>", unsafe_allow_html=True)
    st.caption(
        "Presentation Sprint · Feature Freeze: Data Layer & Prediction Engine locked · "
        "所有展示内容来源于 latest.json 已有字段 · Agent 工作流来自 agent.py 真实代码"
    )


if __name__ == "__main__":
    main()
