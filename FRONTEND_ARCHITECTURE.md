# WC2026 — Frontend Architecture Design Document
**Sprint**: Architecture First · **Author**: Cursor AI (Qoder) · **Date**: 2026-07-05
**Status**: DRAFT — pending CTO review before Sprint 2

---

## 元命令遵守声明

- [x] 本文档为零代码输出，仅分析和设计
- [x] 未修改任何 Python 文件
- [x] 未创建任何 React/Next.js 文件
- [x] 未安装任何 npm 包
- [x] 所有 API 均为建议，不强制后端修改

---

## 一、当前数据流（As-Is）

```
┌─────────────────────────────────────────────────────────────────┐
│                      数据源（Data Sources）                        │
├───────────────┬─────────────────────────────────────────────────┤
│ EloRatings    │ eloratings.net/World.tsv → TTL 7d              │
│ (eloratings)  │ → worldcup_agent/data_layer/cleaned/            │
│               │   ├── elo_live_ratings.json                      │
│               │   └── team_elo_rankings.csv                      │
├───────────────┼─────────────────────────────────────────────────┤
│ FIFA Rankings │ Wiki scraping → cache/fifa_rankings.json          │
│ (data_scraper)│                                                  │
├───────────────┼─────────────────────────────────────────────────┤
│ Team Features │ data_layer/cleaned/teams_2026_enriched.json     │
│ (enrichment) │ → 48 teams, 含 wiki_extract, elo_rating_live    │
├───────────────┼─────────────────────────────────────────────────┤
│ Historical    │ data_layer/cleaned/world_cup_finals_only.csv     │
│ (world_cup)  │ → 448 rows of past WC match outcomes             │
├───────────────┼─────────────────────────────────────────────────┤
│ Odds          │ cache/odds.json                                 │
│ (data_scraper)│                                                  │
└───────────────┴─────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Agent (worldcup_agent/prediction/agent.py)          │
│                                                                  │
│  plan() → search() → execute_tools() → reason() → predict()     │
│                                                                  │
│  ToolRegistry:                                                  │
│    • refresh_elo_ratings()  — calls elo_ratings.py               │
│    • get_team_features()    — reads teams_2026_enriched.json      │
│    • get_historical_matches() — reads world_cup_finals_only.csv  │
│    • check_injury_news()    — placeholder (pending API)          │
│                                                                  │
│  ELOSystem.expected_score():                                     │
│    K_FACTOR=32, HOME_ADVANTAGE=100                              │
│    Formula: win_a = 1/(1+10^((r_b-r_a)/400))                   │
│    Draw: 0.27 * 1/(1+0.009*|diff|) then normalize              │
│                                                                  │
│  ExplainabilityEngine:                                           │
│    ELO diff  → factor key="elo_diff",  contribution=42%          │
│    Rank diff → factor key="rank_diff", contribution=26%          │
└──────────────────────────┬────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│           Snapshot Output (data/snapshots/latest.json)            │
│                                                                  │
│  Schema v2 (from agent.py / prediction_schema.py):              │
│    snapshot_id, generated_at, expires_at,                        │
│    versions: { prediction_version, knowledge_version },         │
│    headline, changes[], matches[], top_upset                    │
│                                                                  │
│  Schema v1 (legacy, from WorldCupAgent):                        │
│    same snapshot_time, champion/runner_up/third_place,           │
│    group_predictions{}, knockout_predictions{},                   │
│    champion_probabilities{}, reasoning_chain[], llm_analysis     │
│                                                                  │
│  ⚠️ 共存问题：两个 schema 并存于不同路径                          │
│     • latest.json (v2): data/snapshots/ ← 当前主用             │
│     • snapshot_p*.json (v1): data/snapshots/ ← 旧格式           │
└──────────────────────────┬────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│              Frontend Consumer (current: explainable_page.py)     │
│                                                                  │
│  技术: Streamlit 1.37.1 (Python)                                │
│  数据消费: 直接读取 latest.json 文件                              │
│  状态: 功能完整，但产品体验不足（Dashboard 风格）                  │
└─────────────────────────────────────────────────────────────────┘
```

### 关键约束

| 约束 | 说明 |
|---|---|
| **无 API 层** | 目前无 HTTP API，前端直接读 JSON 文件 |
| **两套 Schema 共存** | latest.json (v2) + snapshot_p*.json (v1) |
| **Feature Freeze** | 前端禁止修改 agent.py / prediction_schema.py |
| **TTL 控制** | ELO 缓存 7 天，Snapshot 无自动刷新机制 |
| **无 Web 服务** | 当前无 FastAPI/Flask 服务，Streamlit 自带服务器 |

---

## 二、数据契约（Data Contracts）

### 2.1 主快照契约 — `latest.json`（已确认）

**来源**: `agent.py` → `prediction_schema.py` → `save_snapshot()` → `data/snapshots/latest.json`

**更新频率**: 手动触发（`python -m worldcup_agent.prediction.agent`）

**路径优先级**（前端应按此顺序查找）:
1. `./data/snapshots/latest.json`（项目根）
2. `../WorldCupAgent/data/snapshots/latest.json`

```typescript
// ── Snapshot 顶层 ──────────────────────────────────────────────
interface PredictionSnapshot {
  snapshot_id:       string;            // "snap_2026_07_04"
  tournament:        string;            // "FIFA World Cup 2026"
  generated_at:      string;            // ISO 8601
  expires_at:        string;            // ISO 8601 (通常 +24h)
  versions: {
    prediction_version: string;         // "0.2.0"
    knowledge_version:  string;         // git hash 或 "unknown"
  };
  headline:           string;            // 每日简报头句
  changes:           Change[];          // 与上一快照的差异
  matches:           Match[];           // 72 场小组赛预测
  top_upset:         Upset | null;      // 最大冷门信息
  standings:         object;            // ⚠️ 当前为空 {}
}

// ── Change ─────────────────────────────────────────────────────
interface Change {
  match_id:   string;
  teams:      string;                   // "Argentina vs Mexico"
  metric:     "home_win" | "draw" | "away_win";
  prev:       number;                   // 0-1
  curr:       number;                   // 0-1
  delta_pct:  number;                   // e.g. 2.5 (= +2.5pp)
  direction:  "↑" | "↓";
}

// ── Match ───────────────────────────────────────────────────────
interface Match {
  match_id:   string;                   // "wc2026_ARG_MEX"
  home_team:  string;                   // "Argentina"
  away_team:  string;                  // "Mexico"
  kickoff:    string;                  // ISO 8601
  metadata: MatchMetadata;
  prediction: PredictionResult;
  factors:    Factor[];                // 通常 2 个
}

// ── Match Metadata ──────────────────────────────────────────────
interface MatchMetadata {
  prediction_version:  string;
  knowledge_version:  string;
  snapshot_at:        string;           // ISO 8601
  expires_at:         string;           // ISO 8601
  is_stale:           boolean;
}

// ── Prediction Result ───────────────────────────────────────────
interface PredictionResult {
  outcome: Outcome;                     // 三类概率
  predicted_winner: string | null;
  confidence: "high" | "medium" | "low";
  model:      string;                  // "elo_system_v1"
  training_set_size: number;           // 448
  calibration_score: number | null;
}

// ── Outcome ─────────────────────────────────────────────────────
interface Outcome {
  home_win: number;                    // float, 0-1
  draw:     number;
  away_win: number;
}

// ── Factor ──────────────────────────────────────────────────────
interface Factor {
  name:              string;           // "ELO Rating Advantage"
  key:               string;           // "elo_diff"
  value:             number;           // 208 (ELO diff value)
  contribution_pct:  number;           // 0.42 (= 42%)
  direction:         "up" | "down";    // 利好方向
  evidence:          string;           // "Home Elo 2151 vs Away Elo 1943 (diff +208)"
  confidence:        "high" | "medium" | "low";
}
```

### 2.2 团队数据契约 — `teams_2026_enriched.json`

**来源**: `elo_ratings.py` → patch → `data_layer/cleaned/teams_2026_enriched.json`

**用途**: 首页球队展示、ELO 排行榜

```typescript
interface Team {
  team_2026_name:   string;            // "Argentina"
  group:            string;            // "A"
  short_name:       string;            // "ARG"
  country_code:     string;            // "AR"
  elo_rating:       number;            // baseline ELO
  elo_rating_live:  number;            // 来自 eloratings.net
  world_rank_live:  number;            // 来自 eloratings.net
  fifa_ranking_final: number;         // baseline FIFA rank
  wiki_extract:     string;            // 球队简介
  wiki_thumbnail:   string;            // Wikipedia logo URL
  ranking_source:   string;            // "eloratings.net"
}

interface TeamsPayload {
  generated_at: string;                // ISO 8601
  total:        number;                // 48
  teams:        Team[];
}
```

### 2.3 历史赛果契约 — `world_cup_finals_only.csv`

**来源**: `world_cup` data layer

**用途**: 仅训练集规模参考（training_set_size = 448）

⚠️ **前端不应直接消费此文件**，仅在 Metadata 中展示训练集大小。

### 2.4 ELO 排行榜契约 — `team_elo_rankings.csv`

**来源**: `elo_ratings.py` → `data_layer/features/team_elo_rankings.csv`

**用途**: ELO 排行榜展示

```csv
team_2026_name, world_rank, elo_rating, fifa_code
Argentina, 2, 2151, AR
Brazil, 3, 2100, BR
...
```

### 2.5 缺失的数据（需新增 API）

| 数据 | 用途 | 建议 API 端点 | 备注 |
|---|---|---|---|
| 淘汰赛预测 | Knockout 页面 | `GET /api/predictions/knockout` | 需新增 |
| 夺冠概率 | Champion 页面 | `GET /api/predictions/champion` | 需新增 |
| 小组积分榜 | Standings 页面 | `GET /api/standings` | 需新增 |
| 赔率对比 | Odds 比较 | `GET /api/odds/{match_id}` | `cache/odds.json` 已存在 |

---

## 三、前端页面规划（≤ 6 页面）

### 页面结构

```
/
├── Home          — 落地页，5 秒原则
├── Match         — 比赛详情（核心交互页）
├── Group         — 小组赛视图
├── Champion      — 夺冠概率（Optional）
├── About         — Agent 说明
└── Compare       — 今日变化对比（Optional）
```

### 3.1 Home — 落地页

**目标**: 用户进入后 5 秒内回答三个问题：
1. 这是一个什么产品？→ "AI 驱动的世界杯预测 Agent"
2. 今天 AI 预测了什么？→ "阿根廷 vs 墨西哥: 主胜 79.8%"
3. 我下一步应该点击哪里？→ "查看比赛详情"

**布局设计**:

```
┌─────────────────────────────────────────────────────┐
│  [Hero Section]                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │  🤖 WC2026 Prediction Agent                   │ │
│  │  ⚽ FIFA World Cup 2026                       │ │
│  │                                               │ │
│  │  "Upset watch: Spain has a 94% chance..."   │ │
│  │                                               │ │
│  │  🟢 72 matches today   📡 Snapshot v0.2.0   │ │
│  │  Updated: 2026-07-04 22:39                   │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [Featured Match — Top 1 Highlight]                │
│  ┌───────────────────────────────────────────────┐ │
│  │  Argentina  vs  Mexico                        │ │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │  ████████████████████████░░░░  79.8%        │ │
│  │  主胜 79.8%  │  平局 6.7%  │  客胜 13.6%   │ │
│  │                                               │ │
│  │  [🔍 查看完整预测]                             │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [Top 3 今日亮点]                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 🏆 Spain │ │ ⚡ France│ │ 🎯 Brazil│          │
│  │ 94% vs  │ │ 65.8% vs│ │ 63.4% vs│          │
│  │  Qatar  │ │  Tunisia │ │  Serbia  │          │
│  └──────────┘ └──────────┘ └──────────┘          │
│                                                     │
│  [Group Quick Access]                               │
│  A  B  C  D  E  F  G  H  I  J  K  L             │
└─────────────────────────────────────────────────────┘
```

**数据来源**:
- Hero headline → `snapshot.headline`
- 比赛数 → `snapshot.matches.length`
- Featured match → `snapshot.matches[0]`（可按胜率排序取最大热门）
- Top 3 → 按 `home_win` 或 `away_win` 取前三高

### 3.2 Match — 比赛详情（核心页）

**URL**: `/match/[match_id]`（例: `/match/wc2026_ARG_MEX`）

**布局设计**:

```
┌─────────────────────────────────────────────────────┐
│  ← 返回小组赛                                       │
│                                                     │
│  [Match Hero]                                       │
│  ┌───────────────────────────────────────────────┐ │
│  │  Argentina          vs          Mexico         │ │
│  │  FIFA #2  ELO 2151          FIFA #9  ELO 1943│ │
│  │                                               │ │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │
│  │  ██████████████████████████████░░░  79.8%     │ │
│  │  79.8%  │  6.7%  │  13.6%                   │ │
│  │  主胜    │  平局   │  客胜                     │ │
│  │                                               │ │
│  │  预测模型: elo_system_v1  训练样本: 448       │ │
│  │  🟢 高可信                                      │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [Factor Attribution — 核心亮点]                   │
│  ┌───────────────────────────────────────────────┐ │
│  │  🔍 推理因子                                    │ │
│  │                                               │ │
│  │  ELO Rating Advantage      ↑ 42%             │ │
│  │  ████████████████░░░░░░░░░                   │ │
│  │  Home Elo 2151 vs Away Elo 1943 (diff +208)  │ │
│  │  🟢 高可信                                      │ │
│  │                                               │ │
│  │  FIFA World Ranking Adv   ↑ 26%             │ │
│  │  ██████████░░░░░░░░░░░░░░░                   │ │
│  │  Home rank #2 vs Away rank #9                │ │
│  │  🟡 中可信                                      │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [Prediction Metadata]                             │
│  ┌──────────────┬──────────────┬──────────────┐   │
│  │ Snapshot ID  │ Generated    │ Expires      │   │
│  │ snap_2026_  │ 2026-07-04   │ 2026-07-05   │   │
│  │ 07_04       │ 14:39 UTC    │ 14:39 UTC    │   │
│  └──────────────┴──────────────┴──────────────┘   │
│                                                     │
│  [Agent Workflow Timeline]                          │
│  ✅ Plan  ✅ Search  ✅ Load Data  ✅ Reason      │
│  ✅ Predict  ✅ Save                               │
└─────────────────────────────────────────────────────┘
```

**数据来源**:
- 所有数据来自 `snapshot.matches[].*`
- Factor 贡献度条 = `factor.contribution_pct * 100`
- ELO/Rank 数值从 `factor.evidence` 提取或从 `teams_2026_enriched.json` 查询

### 3.3 Group — 小组赛视图

**URL**: `/group/[A-L]`（例: `/group/A`）

**布局**:

```
┌─────────────────────────────────────────────────────┐
│  [Group A — 6 Matches]                             │
│                                                     │
│  [积分榜]                                           │
│  ┌───────────────────────────────────────────────┐ │
│  │ #  Team     P  W  D  L  GD  Pts              │ │
│  │ 1  Argentina 3  3  0  0 +3   9  ← 晋级       │ │
│  │ 2  Mexico    3  2  0  1 +1   6  ← 晋级       │ │
│  │ 3  Ecuador   3  1  0  2 -1   3               │ │
│  │ 4  Jamaica   3  0  0  3 -3   0               │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [比赛列表 — MatchCard 组件]                        │
│  ┌───────────────────────────────────────────────┐ │
│  │ Argentina  vs  Mexico           🟢 79.8%     │ │
│  │ 14:00 UTC  小组第1轮                          │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ Ecuador    vs  Jamaica          🟡 52.4%     │ │
│  │ 14:00 UTC  小组第2轮                          │ │
│  └───────────────────────────────────────────────┘ │
│  ...                                               │
└─────────────────────────────────────────────────────┘
```

**数据来源**:
- 小组比赛 → `snapshot.matches` 中根据 `match_id` 前缀过滤
- 积分榜 ⚠️ → `standings` 当前为空，需新增 API

### 3.4 Champion — 夺冠概率（Optional Component）

**URL**: `/champion`

**布局**:

```
┌─────────────────────────────────────────────────────┐
│  🏆 夺冠概率预测                                    │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ 🔒 待 Data Layer Sprint 新增接口后展示          │ │
│  │                                               │ │
│  │ 当前 snapshot 中无 champion_probabilities 字段 │ │
│  │ 展示 placeholder → 增强公信力（诚实展示）     │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**数据来源**: ⚠️ 当前不存在

### 3.5 About — Agent 说明页

**URL**: `/about`

**内容**:

```
┌─────────────────────────────────────────────────────┐
│  🤖 关于 WC2026 Prediction Agent                   │
│                                                     │
│  [技术栈]                                           │
│  ┌───────────────────────────────────────────────┐ │
│  │  🟢 LangGraph      状态编排框架               │ │
│  │  🟡 Qwen LLM      每日简报生成               │ │
│  │  🟠 ELO System    预测概率引擎               │ │
│  │  🔵 Monte Carlo   淘汰赛模拟（未来）         │ │
│  │  📡 EloRatings   数据来源                   │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [预测流程]                                         │
│  1. Plan — 决定今日预测目标                        │
│  2. Search — 检查数据新鲜度                        │
│  3. Tools — 调用 4 个数据源                        │
│  4. Reason — 构建特征向量                         │
│  5. Predict — ELO + 因子归因                      │
│  6. Save — 持久化快照                             │
│                                                     │
│  [版本信息]                                         │
│  Prediction Version: 0.2.0                        │
│  Knowledge Version: unknown                        │
│  Snapshot ID: snap_2026_07_04                     │
└─────────────────────────────────────────────────────┘
```

### 3.6 Compare — 今日变化（Optional）

**URL**: `/compare`

**布局**:

```
┌─────────────────────────────────────────────────────┐
│  📡 今日概率变化                                    │
│                                                     │
│  与上一个快照对比 · 仅展示变动 > 0.5pp             │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ Argentina vs Mexico                           │ │
│  │ 主胜: 52.3% → 58.8%  ↑ +6.5pp              │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ Spain vs Qatar                                │ │
│  │ 客胜: 11.2% → 13.5%  ↑ +2.3pp              │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**数据来源**:
- `snapshot.changes[]`
- ⚠️ 当前 `changes` 数组为空（无历史快照对比）

---

## 四、API 规划（建议，仅供 CTO 决策）

### 现状

目前**无 HTTP API 层**，前端直接读文件系统。这对于单用户场景足够，但无法：
- 支持多用户并发
- 保护数据层（隐藏内部路径）
- 实现增量更新（只拉变化的部分）

### 建议 API 层

如果未来需要部署为公开 Web 产品，建议新增 FastAPI 层：

```
backend/
└── worldcup_agent/
    ├── prediction/
    │   ├── agent.py           ← 现有，不修改
    │   └── prediction_schema.py ← 现有，不修改
    └── api/
        ├── __init__.py
        ├── routes/
        │   ├── snapshot.py     ← 新增
        │   ├── teams.py        ← 新增
        │   └── health.py       ← 新增
        └── main.py             ← 新增

frontend/
└── (Next.js 15 App Router)
```

**建议端点**:

| 方法 | 端点 | 返回 | 前端用途 |
|---|---|---|---|
| `GET` | `/api/snapshot/latest` | `PredictionSnapshot` | 主数据源 |
| `GET` | `/api/snapshot/{id}` | `PredictionSnapshot` | 历史快照 |
| `GET` | `/api/teams` | `TeamsPayload` | 球队列表/ELO 排行 |
| `GET` | `/api/teams/{name}` | `Team` | 单球队详情 |
| `GET` | `/api/health` | `{status, version}` | 健康检查 |
| `GET` | `/api/standings` | `StandingsPayload` | ⚠️ 待新增 |
| `GET` | `/api/champion` | `ChampionPayload` | ⚠️ 待新增 |
| `GET` | `/api/knockout` | `KnockoutPayload` | ⚠️ 待新增 |

### 数据消费策略

| 策略 | 适用场景 | 前端实现 |
|---|---|---|
| **直接读 JSON 文件** | 当前 Streamlit，部署简单 | `fs.readFile()` 或 fetch |
| **FastAPI + 文件读取** | 未来多用户，隐藏路径 | `GET /api/snapshot/latest` |
| **FastAPI + 数据库** | 未来扩展，支持过滤查询 | `GET /api/matches?group=A&confidence=high` |

⚠️ **决策点**: 本轮是否需要新增 API 层？建议先保持"直接读 JSON"，后续按需升级。

---

## 五、UI Component Tree

```
App
├── Navigation
│   ├── Logo + Title
│   ├── NavLinks: [Home] [Groups] [Champion] [About]
│   └── StatusBadge (Live/Demo)
│
├── HomePage
│   ├── HeroSection
│   │   ├── AgentIdentityBanner  (LangGraph · Qwen · ELO · Monte Carlo)
│   │   ├── HeadlineText         (snapshot.headline)
│   │   ├── SnapshotMeta         (snapshot_id, generated_at, version)
│   │   └── UpdateStatusBadge    (Live / Stale / Updating)
│   │
│   ├── FeaturedMatchCard
│   │   ├── TeamLogos
│   │   ├── WinProbabilityBar    (三段条，同 Streamlit)
│   │   ├── ConfidenceBadge      (High/Medium/Low)
│   │   └── CTAButton            → /match/:id
│   │
│   ├── TopMatchesGrid
│   │   └── MatchCard (3x cards, sorted by highest win prob)
│   │
│   ├── GroupQuickAccess
│   │   └── GroupPill[] (A–L, 12 groups)
│   │
│   └── FooterSection
│       ├── PoweredBy
│       ├── VersionInfo
│       └── DataFreshnessNote
│
├── MatchPage (/match/[match_id])
│   ├── MatchHero
│   │   ├── TeamDisplay (home + away, with ELO/rank)
│   │   ├── WinProbabilityBar (大尺寸版本)
│   │   ├── ConfidenceBadge
│   │   └── ModelInfo (elo_system_v1, 448 样本)
│   │
│   ├── FactorPanel
│   │   ├── FactorChart         (水平条形图，纯 CSS)
│   │   ├── FactorItem[]        (name + contrib% + direction + evidence)
│   │   └── ConfidenceTag
│   │
│   ├── MetadataCard
│   │   ├── SnapshotID
│   │   ├── GeneratedAt
│   │   ├── ExpiresAt
│   │   ├── PredictionVersion
│   │   └── KnowledgeVersion
│   │
│   ├── AgentWorkflowTimeline   (侧边栏或底部)
│   │   └── TimelineStep[] (6 步，已完成状态)
│   │
│   └── RelatedMatches
│       └── MatchCard[] (同小组其他比赛)
│
├── GroupPage (/group/[A-L])
│   ├── GroupHeader (Group A)
│   ├── StandingsTable
│   │   └── StandingsRow[]     ⚠️ 待 API 支持
│   └── GroupMatchList
│       └── MatchCard[]
│
├── ChampionPage (/champion)
│   └── OptionalChampionPanel   (🔒 Graceful Degradation)
│       └── PlaceholderMessage
│
├── AboutPage (/about)
│   ├── AgentIdentitySection
│   ├── TechStackGrid
│   ├── WorkflowTimeline        (6 步详细说明)
│   ├── VersionInfoSection
│   └── DataSourcesSection
│
└── SharedComponents
    ├── MatchCard               (通用比赛卡片)
    │   ├── TeamNames
    │   ├── WinProbabilityBar (compact)
    │   ├── ConfidenceBadge
    │   ├── KickoffTime
    │   └── MatchId
    │
    ├── WinProbabilityBar
    │   ├── HomeSegment
    │   ├── DrawSegment
    │   ├── AwaySegment
    │   └── Labels
    │
    ├── ConfidenceBadge          (High🟢 / Medium🟡 / Low🔴)
    ├── AgentTimeline
    │   └── TimelineStep[]      (Plan · Search · Tools · Reason · Predict · Save)
    │
    ├── FactorBar                (因子贡献度水平条)
    ├── OptionalPlaceholder      (🔒 组件占位)
    └── LoadingStory             (8 步生成过程)
```

---

## 六、技术栈建议

| 层级 | 推荐技术 | 理由 |
|---|---|---|
| **Framework** | Next.js 15 (App Router) | AI Coding 成功率最高，生态成熟 |
| **Language** | TypeScript (strict) | 类型安全，减少 AI 生成 bug |
| **Styling** | Tailwind CSS + CSS Variables | 快速迭代，设计系统友好 |
| **UI 组件库** | shadcn/ui | Radix primitives，可定制，AI 友好 |
| **动画** | Framer Motion | 声明式，可控，非炫技 |
| **图表** | Recharts | React 原生，轻量 |
| **图标** | Lucide React | 统一风格，丰富 |
| **数据获取** | fetch (文件) / SWR | 简单直接，支持缓存 |
| **状态管理** | React Context + useState | 简单场景足够 |
| **部署** | Vercel / Cloudflare Pages | 免费，CDN，全球访问 |

---

## 七、项目目录结构建议（新增 frontend/）

```
WorldCupAgent/                     ← 项目根（现有）
├── worldcup_agent/               ← Python Backend（不修改）
│   ├── prediction/
│   ├── data_layer/
│   └── ...
├── data/                         ← 数据（不修改）
├── frontend/                     ← 新增（⚠️ 本 Sprint 目标）
│   ├── src/
│   │   ├── app/                 ← Next.js App Router
│   │   │   ├── page.tsx          ← Home
│   │   │   ├── layout.tsx        ← Root Layout + Nav
│   │   │   ├── match/
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx ← Match Detail
│   │   │   ├── group/
│   │   │   │   └── [letter]/
│   │   │   │       └── page.tsx ← Group Stage
│   │   │   ├── champion/
│   │   │   │   └── page.tsx
│   │   │   └── about/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/               ← shadcn/ui 组件
│   │   │   ├── MatchCard.tsx
│   │   │   ├── WinProbabilityBar.tsx
│   │   │   ├── FactorChart.tsx
│   │   │   ├── AgentTimeline.tsx
│   │   │   ├── HeroSection.tsx
│   │   │   └── ...
│   │   ├── lib/
│   │   │   ├── snapshot.ts       ← 数据获取函数
│   │   │   ├── types.ts          ← TypeScript interfaces
│   │   │   └── utils.ts
│   │   └── styles/
│   │       └── globals.css
│   ├── public/
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── package.json
│   └── SPEC.md                   ← 设计规范文档
├── tests/                        ← 现有（不修改）
├── documents/                    ← 现有（可补充）
├── explainable_page.py           ← Streamlit（保留，不替换）
└── README.md
```

---

## 八、Design System 基线（参考体育产品）

### 颜色系统

```css
:root {
  /* 背景 */
  --bg:         #0a0e14;   /* 深空黑 — 主背景 */
  --surface:    #131a24;   /* 卡片背景 */
  --surface2:   #1a2333;   /* 悬停/次级卡片 */
  --border:     #1e2a3a;   /* 边框 */

  /* 文本 */
  --text:       #cdd9e5;   /* 主文本 */
  --muted:      #768390;   /* 次级文本 */

  /* 强调色 */
  --accent:     #58a6ff;   /* 主蓝 — 交互/链接 */
  --green:      #3fb950;   /* 高可信/主胜 */
  --yellow:     #d29922;   /* 中可信/平局 */
  --red:        #f85149;   /* 低可信/客胜 */
  --orange:     #e8854a;   /* 客胜备选色 */
  --purple:     #bc8cff;   /* 特殊状态 */
}
```

### 字体

```
主字体:  Inter (400/500/600/700/800)
等宽:    JetBrains Mono (400/500)
字重层级:
  - Hero 标题:  800, 2rem
  - 卡片标题:   700, 1.1rem
  - 身体文本:   400, 0.88rem
  - Label:      600, 0.7rem (大写, 字间距 0.1em)
  - Mono:       400, 0.72rem
```

### 间距与圆角

```
间距基准: 4px
卡片圆角: 16px
按钮圆角: 10px
Badge 圆角: 20px
间距递进: 4, 8, 12, 16, 24, 32, 48px
```

### 动画原则（参考体育产品）

| 允许 | 禁止 |
|---|---|
| 数字滚动（0 → 79.8%，1.2s） | 满屏粒子效果 |
| 卡片浮起（translateY -2px） | 旋转 Logo |
| 页面切换（fade + slide，0.3s） | 自动闪烁 |
| 概率条增长（width 动画） | 炫光/Glow 特效 |
| Timeline 步骤依次点亮 | 无关视觉噪声 |

---

## 九、5 秒原则验证清单

每个页面必须通过以下验证：

| 问题 | Home | Match | Group | Champion | About |
|---|---|---|---|---|---|
| 用户知道这是世界杯 AI 预测？ | ✅ Hero + Headline | ✅ Match Hero | ✅ Group Header | ⚠️ 待 API | ✅ Agent Banner |
| 用户知道今天的预测结论？ | ✅ Featured Match | ✅ Win bar | ⚠️ 需选组 | ⚠️ 待 API | N/A |
| 用户知道下一步点击哪里？ | ✅ CTA Button | ✅ Factor Panel | ✅ Match Cards | ⚠️ 待 API | N/A |
| 页面是否有产品感（非 Demo）？ | ⚠️ 需 Next.js 重构 | ⚠️ 需优化 | ⚠️ 需优化 | ⚠️ 待 API | ⚠️ 需优化 |

---

## 十、Backend Freeze 声明（待确认）

```text
禁止修改以下文件及目录：

❌ worldcup_agent/prediction/agent.py
❌ worldcup_agent/prediction/prediction_schema.py
❌ worldcup_agent/prediction/elo_system.py
❌ worldcup_agent/elo_ratings.py
❌ worldcup_agent/data_layer/
❌ data/snapshots/
❌ data/cache/
❌ tests/

如需新 API，输出「新增 API 建议」并等待确认。
```

---

## 十一、下一步（Sprint 2 待确认）

```
Sprint 2: Design Sprint
├── Step 1: 确认 Frontend Architecture Document
├── Step 2: UI/UX Design（参考 ESPN/Sofascore/Apple Sports）
├── Step 3: 输出完整 UI Spec（颜色/字体/间距/动画/组件）
└── Step 4: High-Fidelity Prototype（HTML Static，不接 API）
```
