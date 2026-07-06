# WC2026 AI Prediction Agent

**Not only predicts the World Cup champion — explains every prediction.**

An AI agent that generates daily predictions for all 104 matches in the 2026 FIFA World Cup, with full explainability. Every prediction includes factor attribution showing exactly why the AI believes one team will win.

## Live Demo

> **Frontend**: Next.js app at `http://localhost:3000`
>
> **Demo Page**: `http://localhost:3000/demo` - Interactive bilingual showcase
>
> **Agent**: Run `python -m worldcup_agent.prediction.agent` for daily predictions

## Features

### Core Capabilities

- **Daily Predictions**: 104 matches with win/draw/lose probabilities
- **Factor Attribution**: Each prediction includes ranked factors (ELO, FIFA Ranking, Recent Form) with percentage contributions
- **LLM-Powered Reasoning**: Uses Qwen LLM to generate natural language explanations
- **Bilingual Support**: Full Chinese/English interface with instant switching
- **Versioned Snapshots**: Every prediction snapshot records version history for comparison

### Modern Frontend

- **Next.js 16 with Turbopack**: Lightning-fast development and builds
- **Real-time Language Toggle**: Switch between Chinese and English instantly
- **Responsive Design**: Mobile-first approach with dark theme
- **Interactive Components**: Animated cards, hover effects, and smooth transitions
- **Knowledge Layer**: 48 teams, 60+ players, 48 coaches with detailed profiles

### Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WC2026 Agent System                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ Data Agent  │→ │Analysis Agent│→│Simulation Agent│   │
│  │ (Elo, Odds)│  │ (Strength)   │  │ (Monte Carlo)   │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│         ↓                ↓                  ↓              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Cognitive World Model (NEW)                │   │
│  │  • Belief-Uncertainty-Evidence cognitive model       │   │
│  │  • Goal-driven autonomous agents                     │   │
│  │  • Adversarial debate between agents                 │   │
│  └─────────────────────────────────────────────────────┘   │
│         ↓                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ReflectionAgent│→ │ExplainerAgent│→│  Quality Agent  │   │
│  │ (Self-check) │  │ (Narratives) │  │ (QA checks)    │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Explainability Example

```
Argentina vs Mexico
─────────────────
  H: 80%   D: 7%   A: 13%

Top Factors:
  ↑ 42%  ELO Rating Advantage
          Home Elo 2129 vs Away Elo 1912 (diff +217)

  ↑ 26%  FIFA World Ranking
          Home rank #3 vs Away rank #28
```

## Quick Start

### 1. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit:
- **Main App**: http://localhost:3000
- **Demo Page**: http://localhost:3000/demo

### 2. Generate Predictions

```bash
# Single run
python -m worldcup_agent.prediction.agent

# Force refresh data
python -m worldcup_agent.prediction.agent --force-refresh

# Continuous loop (production mode)
python -m worldcup_agent.prediction.agent --loop --interval 3600
```

### 3. Access Data

```python
from worldcup_agent.prediction import get_latest_snapshot, PredictionSnapshot

# Load latest predictions
snap = get_latest_snapshot()
for match in snap.match_predictions[:3]:
    print(f"{match.home_team} vs {match.away_team}")
    print(f"  H: {match.outcome.home_win:.0%}  D: {match.outcome.draw:.0%}  A: {match.outcome.away_win:.0%}")
```

## Project Structure

```
WorldCupAgent/
├── worldcup_agent/
│   ├── prediction/          # Prediction pipeline
│   │   ├── agent.py       # Main agent orchestrator
│   │   ├── world_state.py # Tournament state tracking
│   │   ├── observer.py    # Data observation system
│   │   ├── elo_system.py  # Elo probability model
│   │   └── prediction_schema.py  # Versioned data schemas
│   ├── multi_agent/       # Multi-agent system
│   │   ├── core.py       # WorldState, BaseAgent, Orchestrator
│   │   ├── cognitive_model.py   # Belief-Uncertainty-Evidence
│   │   ├── goal_agent.py        # Goal-driven autonomy
│   │   ├── debate_mechanism.py  # Adversarial collaboration
│   │   └── agents/       # 6 specialized agents
│   └── tournament/         # Tournament rules engine
│       ├── rule.py        # FIFA 2026 rules (Tiebreakers, R32)
│       └── knockout_simulator.py  # Bracket simulation
├── frontend/              # Next.js 16 application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Main page
│   │   │   └── demo/page.tsx     # Demo showcase page
│   │   ├── components/
│   │   │   ├── TeamComponents.tsx    # Team cards & match cards
│   │   │   ├── PlayerComponents.tsx  # Player cards
│   │   │   └── LanguageSwitcher.tsx  # Language toggle
│   │   ├── i18n/                  # Internationalization
│   │   │   ├── index.tsx
│   │   │   ├── zh.json
│   │   │   └── en.json
│   │   └── knowledge/             # Football knowledge layer
│   │       ├── teams_knowledge.json   # 48 teams data
│   │       ├── players_knowledge.json # 60+ players data
│   │       ├── coaches_knowledge.json # 48 coaches data
│   │       └── types.ts
│   └── public/
├── data/
│   ├── snapshots/         # Prediction snapshots
│   └── cache/             # Cached data (Elo, Odds)
├── explainable_page.py  # Streamlit visualization (legacy)
└── elo_ratings.py      # Elo data scraper
```

## Frontend Features

### Demo Page Components

| Component | Description |
|-----------|-------------|
| Hero Section | Gradient background with live stats |
| Match Card | Featured match with probability bars |
| Team Cards | AI-powered team analysis |
| Player Cards | Key player statistics |
| Translation Showcase | Bilingual UI examples |

### Knowledge Layer

The frontend includes a comprehensive knowledge layer with:

- **48 Teams**: Full profiles with tactical analysis
- **60+ Players**: Performance stats and highlights
- **48 Coaches**: Tactical philosophy and achievements

### Bilingual Support

```tsx
// Component usage
const { locale, t } = useI18n();

// Switch languages
<span>{t("prediction.home_win")}</span>
// ZH: 主场胜 | EN: Home Win
```

## Architecture Highlights

### 1. Belief-Uncertainty-Evidence Model

Every prediction is stored as a `Belief` with:
- **Confidence Score**: 0-1 probability
- **Evidence Chain**: Sources that support the prediction
- **Uncertainty Type**: Epistemic (lack of knowledge) vs Aleatoric (inherent randomness)

```python
from worldcup_agent.multi_agent import CognitiveWorldModel, Evidence, EvidenceSource

model = CognitiveWorldModel()
model.assert_belief(
    subject="argentina_vs_mexico",
    predicate="home_win_prob",
    value=0.80,
    confidence=0.75,
    evidence=[
        Evidence(source=EvidenceSource.ELO_RATING, weight=0.45, quality="high"),
        Evidence(source=EvidenceSource.SIMULATION, weight=0.35, quality="medium"),
    ]
)
```

### 2. Goal-Driven Agents

Agents declare goals and autonomously decide next steps:

```python
from worldcup_agent.multi_agent import GoalDrivenAgent, GoalType

agent = SimulationAgent()
goal = agent.declare_goal(
    goal_type=GoalType.SIMULATE,
    description="Predict tournament winner",
    success_criteria=["confidence_above_0.7", "has_evidence"]
)
# Agent autonomously decides: CONTINUE / RETRY / REQUEST_HELP / ESCALATE
```

### 3. Adversarial Debate

When agents disagree, structured debates resolve conflicts:

```python
from worldcup_agent.multi_agent import DebateManager, PositionSide

manager = DebateManager(cognitive_model)
debate = manager.debate_prediction(
    subject="argentina_champion",
    proponent="simulation_agent",
    opponent="analysis_agent",
    pro_value=0.25,
    con_value=0.30,
)
manager.judge_debate(debate.id)
# Returns verdict with reasoning
```

## Data Schema

### Prediction Snapshot

```json
{
  "snapshot_id": "snap_2026_07_05_0921",
  "tournament": "FIFA World Cup 2026",
  "generated_at": "2026-07-05T09:21:42Z",
  "versions": {
    "prediction_version": "0.2.0",
    "knowledge_version": "abc12345"
  },
  "headline": "Upset watch: Spain has a 92% chance...",
  "matches": [
    {
      "match_id": "wc2026_ARG_MEX",
      "home_team": "Argentina",
      "away_team": "Mexico",
      "prediction": {
        "outcome": {"home_win": 0.80, "draw": 0.07, "away_win": 0.13},
        "confidence": "high"
      },
      "factors": [
        {
          "name": "ELO Rating Advantage",
          "contribution_pct": 0.42,
          "evidence": "Home Elo 2129 vs Away Elo 1912 (diff +217)"
        }
      ]
    }
  ]
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHSCOPE_API_KEY` | - | Alibaba Cloud API key for LLM |
| `ELO_CACHE_TTL_HOURS` | 168 | Elo cache TTL (7 days) |

### Frontend Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Next.js | 16.x | React framework |
| Tailwind CSS | 3.x | Styling |
| TypeScript | 5.x | Type safety |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.3.0 | 2026-07-06 | Next.js 16 frontend with bilingual UI, modern glass-morphism design |
| 0.2.0 | 2026-07-05 | Elo ratings (S9) integrated; FactorAttribution schema; versioned snapshots |
| 0.1.0 | 2026-06-01 | Initial release: sequential pipeline, Monte Carlo simulation |

## Documentation

- [PRODUCT_SPEC.md](./PRODUCT_SPEC.md) - Product specification
- [TOURNAMENT_RULE_SPEC.md](./TOURNAMENT_RULE_SPEC.md) - FIFA 2026 rules
- [TOURNAMENT_TRACE_SPEC.md](./TOURNAMENT_TRACE_SPEC.md) - Explainability trace format
- [ENGINEERING_GUIDELINES.md](./ENGINEERING_GUIDELINES.md) - Engineering standards

## License

MIT License
