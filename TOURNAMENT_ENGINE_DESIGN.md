# Tournament Presentation Design
**Sprint**: TP — Tournament Presentation · **Author**: Cursor AI (Qoder) · **Date**: 2026-07-05
**Status**: DESIGN v2 — 重写版（依据 CTO 审批意见）

---

## 元声明

- 本文档为零代码输出，仅分析和设计
- **不新增**任何 JSON 数据文件
- **不重新生成** reasoning
- **不重新运行** Monte Carlo
- **只做**：ViewModel 构建 + Narrative 组合 + React 展示

---

## CTO 审批结果

| 事项 | 审批 | 原因 |
|---|---|---|
| tournament_engine.json | ❌ 不批准 | 制造第二个数据源，破坏 Single Source of Truth |
| tournament_engine.py（新预测引擎） | ❌ 不批准 | Engine 已存在（Monte Carlo），无需重建 |
| round_reasoning（重新生成） | ❌ 不批准 | 重新生成 = Hallucination，不是真实推理 |
| 时间戳关联 reasoning | ❌ 不批准 | 时间戳脆弱，MatchID 更稳定 |
| Tournament View Builder | ✅ 批准 | 只整理，不生产 |
| Champion Narrative Builder | ✅ 批准 | 组合已有 reasoning，生成叙事 |
| Interactive Bracket | ✅ 批准 | React 展示赛程树 |

---

## 二、CTO 补充审批（v2）

| 补充事项 | 审批 | 说明 |
|---|---|---|
| ViewModel 写成 UI Adapter | ✅ 要求 | MatchCardViewModel 等，不是 Data Mapper |
| Champion Narrative 改为 Story Timeline | ✅ 要求 | 按 Group→R16→QF→SF→Final 叙事 |
| Bracket 节点 Hover/Click 展开 | ✅ 要求 | 展开 Prediction/Confidence/Factors/Reasoning |
| 组件分层架构 | ✅ 要求 | Presentation → Business → UI |
| TP-1 改为 Frontend Foundation | ✅ 要求 | Types + Loader + ViewModel + Skeleton + Route |
| AI Prediction Confidence Explain | ✅ 新增 | 点击展开置信度解释 |
| Replay Prediction | ✅ 新增 | 20 秒自动播放赛程动画 |

---

## 三、ViewModel 架构：UI Adapter 模式

### 3.1 Data Mapper vs UI Adapter

```
❌ Data Mapper（不推荐）：
  interface MatchCardData {
    home_team: string;
    away_team: string;
    home_win_prob: number;
    ...
  }
  // 直接映射，无语义，跨组件难以复用

✅ UI Adapter（推荐）：
  interface MatchCardViewModel {
    title: string;              // "Argentina vs Mexico"
    subtitle: string;           // "Group A · Round 1"
    prediction: {
      homeWin: number;         // 0.588
      draw: number;             // 0.221
      awayWin: number;         // 0.191
    };
    confidence: "High" | "Medium" | "Low";
    factors: FactorCardViewModel[];
    status: "Upcoming" | "Live" | "Finished";
    reasoning: string;          // 引用已有
    snapshot: SnapshotBadgeViewModel;
  }
  // 有语义，跨组件复用，维护成本低
```

### 3.2 ViewModel 目录结构

```
❌ 错误：
  latest.json + tournament_engine.json + another.json + ...

✅ 正确：
  latest.json（唯一数据源）
       ↓
  Loader（snapshot.loader.ts）
       ↓
  Adapter（snapshot.adapter.ts，可选）
       ↓
  ViewModel（TypeScript，仅读取）
       ↓
  React UI（展示）
```

### 1.2 Loader + Adapter + ViewModel 职责

```
Loader（snapshot.loader.ts）：
  ✓ 读取 latest.json 文件
  ✓ 类型检查
  ✓ 错误处理（NOT_FOUND / PARSE_ERROR）
  ✗ 不做数据转换

Adapter（snapshot.adapter.ts）：
  ✓ latest.json → 中间格式
  ✓ 未来 FastAPI 可复用
  ✗ 不做 UI 逻辑

ViewModel：
  ✓ 消费 Loader/Adapter 输出
  ✓ 生成 UI 模型（MatchCardViewModel 等）
  ✓ 格式化、语义化
  ✗ 不直接读文件
  ✗ 不做 fetch
```

### 1.3 ViewModel = 整理，不是生产

```
ViewModel 做什么：
  ✓ 读取 latest.json
  ✓ 按 MatchID 索引 reasoning
  ✓ 按 MatchID 索引 factors
  ✓ 构建 Bracket 树结构
  ✓ 组合 Champion Narrative
  ✓ 生成 UI 消费模型（TypeScript interfaces）

ViewModel 不做什么：
  ✗ 不计算积分（已有 latest.json）
  ✗ 不生成 reasoning（已有 latest.json）
  ✗ 不运行 Monte Carlo（已有 latest.json）
  ✗ 不保存新 JSON 文件
  ✗ 不发明新数据
```

### 1.4 Narrative = 组合，不是生成

```
❌ 错误：
  AI 重新生成 → "Argentina 2-1 France because..."

✅ 正确：
  AI 组合已有 → "Argentina vs France，胜率 51.4%，
                 reasoning 引用：'Argentina 主场优势明显，ELO 差值显著'
                 reasoning 引用：'Argentina（强队，实力72.3）'"
```

---

## 二、数据来源（仅 latest.json）

### 2.1 关键字段索引

```typescript
// latest.json 中可直接消费的字段

interface LatestJsonKeyFields {
  // 小组赛
  "group_predictions": {
    [group: string]: {
      "matches": Array<{
        "id": string;                          // "A_match_1"
        "home_team": string;
        "away_team": string;
        "home_win_prob": string;               // "58.8%"
        "draw_prob": string;
        "away_win_prob": string;
        "reasoning": string;                   // ← 真实推理文本
        "stage": string;                       // "A组第1轮"
        "round_number": number;
      }>;
      "standings": Array<{
        "team": string;
        "played": number;
        "won": number;
        "drawn": number;
        "lost": number;
        "goals_for": number;
        "goals_against": number;
        "goal_diff": number;
        "points": number;
      }>;
      "qualifiers": string[];                 // ["Argentina", "Mexico"]
    };
  };

  // 淘汰赛
  "knockout_predictions": {
    "predicted_champion": string;             // "Argentina"
    "champion_probability": string;            // "100.0%"
    "rounds": {
      "round_of_16": Array<{...}>;
      "quarter_finals": Array<{...}>;
      "semi_finals": Array<{...}>;
      "third_place": {...};
      "final": {...};
    };
    "champion_probabilities": {
      [team: string]: string;                 // "10000/10000 (100.0%)"
    };
  };

  // Monte Carlo 统计
  "monte_carlo_simulations": number;          // 10000
  "reasoning_chain": Array<{
    "tool": string;                           // "monte_carlo_tool"
    "action": string;                         // "simulate_knockout"
    "result": string;                         // "Champion: Argentina (100.0%)"
    "duration_ms": number;                    // 3988253
    "timestamp": string;
  }>;

  // LLM 分析（可引用）
  "llm_analysis": string;                    // Qwen LLM 输出
}
```

### 2.2 MatchID 命名规则（已存在）

```
小组赛：{group}_match_{n}
  例：A_match_1, A_match_2, ..., A_match_6

淘汰赛：{stage}_{id}
  例：r16_top_0, qf_0, sf_0, final, third
```

---

## 三、Tournament ViewModel（TypeScript）

### 3.1 架构

```
frontend/src/lib/tournament/
├── viewModel.ts          ← 核心 ViewModel（读 latest.json，构建 UI 模型）
├── types.ts             ← UI 层 TypeScript interfaces
├── bracketBuilder.ts    ← Bracket 树构建器
├── narrativeBuilder.ts  ← Champion Narrative 组合器
└── matchIdMap.ts       ← MatchID → Reasoning 映射表
```

### 3.2 ViewModel 目录结构

```
frontend/src/lib/tournament/
├── types/
│   ├── latest-json.types.ts      ← latest.json 原始类型
│   ├── ui-adapter.types.ts       ← UI Adapter 类型
│   └── index.ts
├── loader.ts                     ← Data Loader（读 latest.json）
├── viewModels/
│   ├── matchCard.vm.ts           ← MatchCardViewModel
│   ├── championPath.vm.ts        ← ChampionPathViewModel
│   ├── bracketNode.vm.ts         ← BracketNodeViewModel
│   ├── confidenceExplain.vm.ts   ← ConfidenceExplainViewModel
│   └── index.ts
├── builders/
│   ├── groupStage.builder.ts     ← 小组赛 Builder
│   ├── knockout.builder.ts        ← 淘汰赛 Builder
│   ├── championNarrative.builder.ts ← Story Timeline Builder
│   └── index.ts
└── index.ts
```

### 3.3 UI Adapter 示例

```typescript
// matchCard.vm.ts

export interface MatchCardViewModel {
  // 基础信息
  matchId: string;
  title: string;                    // "Argentina vs Mexico"
  subtitle: string;                 // "Group A · Round 1"
  kickoff: string;                  // "2026-07-14 14:00 UTC"

  // 预测结果
  prediction: {
    homeWin: number;               // 0.588
    draw: number;                   // 0.221
    awayWin: number;               // 0.191
    predictedWinner: string;       // "Argentina"
    predictedScore: string;        // "2-1"（占位）
    hasRealScore: boolean;         // false（比分不可信）
  };

  // 置信度
  confidence: {
    level: "High" | "Medium" | "Low";
    score: number;                  // 0-100
    explanation: ConfidenceExplainViewModel;
  };

  // 推理因子
  factors: FactorCardViewModel[];

  // Reasoning 引用
  reasoning: {
    text: string;                  // 引用已有 reasoning
    source: string;                 // "group_prediction_tool"
    isVerified: boolean;           // true
  };

  // Snapshot
  snapshot: SnapshotBadgeViewModel;

  // 状态
  status: "Upcoming" | "Live" | "Finished";
}

export interface FactorCardViewModel {
  name: string;                    // "ELO Rating Advantage"
  contribution: number;             // 0.42 (42%)
  direction: "up" | "down";        // 对主队有利方向
  evidence: string;                 // "Home Elo 2151 vs Away Elo 1943"
  confidence: "High" | "Medium" | "Low";
}

export interface ConfidenceExplainViewModel {
  score: number;                   // 87
  level: "High" | "Medium" | "Low";
  reasons: {
    label: string;                 // "Recent form stable"
    status: "pass" | "warn" | "fail";
    detail: string;               // "Last 10 A-matches: 7W 2D 1L"
  }[];
  monteCarlo: {
    iterations: number;            // 10000
    convergenceReached: boolean;   // true
  };
}

export interface ReplayControlsViewModel {
  // 播放状态
  isPlaying: boolean;
  currentTime: number;            // 0-20（秒）
  duration: number;              // 20（秒）

  // 速度
  playbackRate: 0.5 | 1 | 2;

  // 进度
  progress: number;               // 0-1（百分比）
  currentTimeDisplay: string;    // "0:12"
  durationDisplay: string;        // "0:20"

  // 方法
  play(): void;
  pause(): void;
  restart(): void;
  seek(time: number): void;
  setPlaybackRate(rate: 0.5 | 1 | 2): void;
}

export interface SnapshotBadgeViewModel {
  id: string;                      // "snap_2026_07_04"
  generatedAt: string;             // "2026-07-04T18:08:38"
  version: string;                 // "v20260704_1008"
  expiresAt: string;               // "2026-07-04T23:59:59"
  status: "Live" | "Stale";       // 根据时间判断
}
```

```typescript
// viewModel.ts

import type { LatestJson } from "./types";

export class TournamentViewModel {
  private data: LatestJson;

  constructor(latestJson: LatestJson) {
    this.data = latestJson;
  }

  // ── Group Stage ──────────────────────────────────────────────

  getGroupStage(): GroupStageView {
    const groups: GroupStageGroup[] = [];

    for (const [letter, group] of Object.entries(this.data.group_predictions)) {
      groups.push({
        letter,
        matches: group.matches.map((m) => ({
          matchId: m.id,
          homeTeam: m.home_team,
          awayTeam: m.away_team,
          homeWinProb: parseFloat(m.home_win_prob),
          drawProb: parseFloat(m.draw_prob),
          awayWinProb: parseFloat(m.away_win_prob),
          reasoning: m.reasoning,          // ← 直接引用，不生成
          stage: m.stage,
        })),
        standings: group.standings,
        qualifiers: group.qualifiers,
      });
    }

    return { groups };
  }

  // ── Knockout Bracket ─────────────────────────────────────────

  getKnockoutBracket(): KnockoutBracketView {
    const { rounds } = this.data.knockout_predictions;

    return {
      roundOf16: rounds.round_of_16.map(this._mapKnockoutMatch),
      quarterFinals: rounds.quarter_finals.map(this._mapKnockoutMatch),
      semiFinals: rounds.semi_finals.map(this._mapKnockoutMatch),
      thirdPlace: this._mapKnockoutMatch(rounds.third_place),
      final: this._mapKnockoutMatch(rounds.final),
    };
  }

  private _mapKnockoutMatch(m: any): KnockoutMatchView {
    return {
      matchId: m.id,
      homeTeam: m.home_team,
      awayTeam: m.away_team,
      homeWinProb: parseFloat(m.home_win_prob),
      drawProb: parseFloat(m.draw_prob),
      awayWinProb: parseFloat(m.away_win_prob),
      reasoning: m.reasoning,              // ← 直接引用，不生成
      predictedScore: m.predicted_score,   // ⚠️ 占位比分，前端标注"预测"
    };
  }

  // ── Champion Path ────────────────────────────────────────────

  getChampionPath(): ChampionPathView {
    const { knockout_predictions, reasoning_chain, monte_carlo_simulations } = this.data;

    const champion = knockout_predictions.predicted_champion;
    const probability = parseFloat(knockout_predictions.champion_probability) / 100;

    // 从 reasoning_chain 获取 Monte Carlo 统计
    const monteCarloStep = reasoning_chain.find(
      (s) => s.tool === "monte_carlo_tool"
    );
    const durationSec = monteCarloStep
      ? Math.round(monteCarloStep.duration_ms / 1000)
      : 0;

    // 构建冠军路径（从淘汰赛结果回溯）
    const legs = this._buildChampionLegs(champion);

    // 组合叙事（引用已有 reasoning，不生成新文本）
    const narrative = this._buildChampionNarrative(champion, legs, probability);

    return {
      champion,
      probability,
      monteCarlo: {
        iterations: monte_carlo_simulations,
        wins: monte_carlo_simulations,    // 当前 100% 夺冠
        total: monte_carlo_simulations,
        durationSec,
      },
      legs,
      narrative,
    };
  }

  private _buildChampionLegs(champion: string): ChampionLegView[] {
    const { rounds } = this.data.knockout_predictions;
    const legs: ChampionLegView[] = [];

    // R16
    const r16Match = rounds.round_of_16.find(
      (m) => m.home_team === champion || m.away_team === champion
    );
    if (r16Match) {
      const isHome = r16Match.home_team === champion;
      legs.push({
        stage: "round_of_16",
        stageLabel: "1/8决赛",
        vs: isHome ? r16Match.away_team : r16Match.home_team,
        winProb: isHome
          ? parseFloat(r16Match.home_win_prob)
          : parseFloat(r16Match.away_win_prob),
        reasoning: r16Match.reasoning,  // ← 直接引用已有
        matchId: r16Match.id,
      });
    }

    // QF
    const qfMatch = rounds.quarter_finals.find(
      (m) => m.home_team === champion || m.away_team === champion
    );
    if (qfMatch) {
      const isHome = qfMatch.home_team === champion;
      legs.push({
        stage: "quarter_final",
        stageLabel: "1/4决赛",
        vs: isHome ? qfMatch.away_team : qfMatch.home_team,
        winProb: isHome
          ? parseFloat(qfMatch.home_win_prob)
          : parseFloat(qfMatch.away_win_prob),
        reasoning: qfMatch.reasoning,
        matchId: qfMatch.id,
      });
    }

    // SF
    const sfMatch = rounds.semi_finals.find(
      (m) => m.home_team === champion || m.away_team === champion
    );
    if (sfMatch) {
      const isHome = sfMatch.home_team === champion;
      legs.push({
        stage: "semi_final",
        stageLabel: "半决赛",
        vs: isHome ? sfMatch.away_team : sfMatch.home_team,
        winProb: isHome
          ? parseFloat(sfMatch.home_win_prob)
          : parseFloat(sfMatch.away_win_prob),
        reasoning: sfMatch.reasoning,
        matchId: sfMatch.id,
      });
    }

    // Final
    const finalMatch = rounds.final;
    const isHome = finalMatch.home_team === champion;
    legs.push({
      stage: "final",
      stageLabel: "决赛",
      vs: isHome ? finalMatch.away_team : finalMatch.home_team,
      winProb: isHome
        ? parseFloat(finalMatch.home_win_prob)
        : parseFloat(finalMatch.away_win_prob),
      reasoning: finalMatch.reasoning,
      matchId: finalMatch.id,
    });

    return legs;
  }

  private _buildChampionNarrative(
    champion: string,
    legs: ChampionLegView[],
    probability: number
  ): string {
    // 组合已有 reasoning，生成叙事
    // ⚠️ 不生成新文本，只组合已有文本

    const pathSteps = legs
      .map((leg) => `${leg.stageLabel} 战胜 ${leg.vs}（胜率 ${(leg.winProb * 100).toFixed(1)}%）`)
      .join(" → ");

    return `${champion} 晋级路径：${pathSteps}`;
  }
}
```

### 3.3 UI 层 Interfaces

```typescript
// types.ts

export interface GroupStageView {
  groups: GroupStageGroup[];
}

export interface GroupStageGroup {
  letter: string;
  matches: GroupMatchView[];
  standings: Standing[];
  qualifiers: string[];
}

export interface GroupMatchView {
  matchId: string;
  homeTeam: string;
  awayTeam: string;
  homeWinProb: number;    // 0-1
  drawProb: number;
  awayWinProb: number;
  reasoning: string;      // ← 直接引用已有
  stage: string;
}

export interface KnockoutBracketView {
  roundOf16: KnockoutMatchView[];
  quarterFinals: KnockoutMatchView[];
  semiFinals: KnockoutMatchView[];
  thirdPlace: KnockoutMatchView;
  final: KnockoutMatchView;
}

export interface KnockoutMatchView {
  matchId: string;
  homeTeam: string;
  awayTeam: string;
  homeWinProb: number;
  drawProb: number;
  awayWinProb: number;
  reasoning: string;      // ← 直接引用已有
  predictedScore: string;  // ⚠️ 占位比分，前端标注"预测"
}

export interface ChampionPathView {
  champion: string;
  probability: number;    // 0-1
  monteCarlo: {
    iterations: number;
    wins: number;
    total: number;
    durationSec: number;
  };
  legs: ChampionLegView[];
  narrative: string;
}

export interface ChampionLegView {
  stage: string;
  stageLabel: string;
  vs: string;
  winProb: number;         // 0-1，无比分
  reasoning: string;        // ← 直接引用已有
  matchId: string;
}

export interface MonteCarloStatsView {
  iterations: number;
  championDistribution: Record<string, number>;
  durationSec: number;
  narrative: string;
}
```

### 3.4 Narrative Builder

```typescript
// narrativeBuilder.ts

import type { ChampionPathView, LatestJson } from "./types";

export class NarrativeBuilder {
  // 组合 Champion Narrative
  // 原则：引用已有 reasoning，不生成新文本

  buildChampionNarrative(path: ChampionPathView): string {
    const { champion, probability, legs, monteCarlo } = path;

    const probPct = (probability * 100).toFixed(1);
    const durationMin = Math.floor(monteCarlo.durationSec / 60);
    const durationSecRem = monteCarlo.durationSec % 60;

    const pathDesc = legs
      .map((leg) => `${leg.stageLabel} vs ${leg.vs}（${(leg.winProb * 100).toFixed(1)}%）`)
      .join(" → ");

    return [
      `🏆 ${champion} 夺冠概率：${probPct}%`,
      `📊 Monte Carlo：${monteCarlo.iterations.toLocaleString()} 次模拟 · 耗时 ${durationMin}m ${durationSecRem}s`,
      `📍 晋级路径：${pathDesc}`,
    ].join("\n");
  }

  // 构建单场 Reasoning Narrative
  buildMatchNarrative(matchId: string, reasoning: string): string {
    // 直接引用已有 reasoning
    return reasoning || "暂无推理依据";
  }

  // 构建 R16 对阵来源说明
  buildPairingExplanation(
    groupQualifiers: Record<string, string[]>
  ): string {
    const explanations: string[] = [];

    const topHalf = [
      ["A", "B"], ["C", "D"], ["E", "F"], ["G", "H"],
    ];
    const bottomHalf = [
      ["I", "J"], ["K", "L"],
    ];

    for (const [g1, g2] of topHalf) {
      const q1 = groupQualifiers[g1]?.[0];
      const q2 = groupQualifiers[g2]?.[1];
      if (q1 && q2) {
        explanations.push(`${g1}组第1(${q1}) vs ${g2}组第2(${q2})`);
      }
    }

    for (const [g1, g2] of bottomHalf) {
      const q1 = groupQualifiers[g1]?.[0];
      const q2 = groupQualifiers[g2]?.[1];
      if (q1 && q2) {
        explanations.push(`${g1}组第1(${q1}) vs ${g2}组第2(${q2})`);
      }
    }

    return explanations.join(" | ");
  }
}
```

---

## 四、Sprint 拆分（TP-1 / TP-2 / TP-3）

### TP-1：Frontend Foundation（约 2 小时）

**目标**：建立前端工程基础，包括 Types + Loader + ViewModel + Skeleton + Route

**交付物**：
```
frontend/src/
├── lib/tournament/
│   ├── types/
│   │   ├── latest-json.types.ts      ← latest.json 原始类型
│   │   └── ui-adapter.types.ts     ← UI Adapter 类型
│   ├── loader.ts                     ← Data Loader
│   ├── viewModels/
│   │   ├── matchCard.vm.ts          ← MatchCardViewModel
│   │   ├── championPath.vm.ts        ← ChampionPathViewModel
│   │   ├── bracketNode.vm.ts         ← BracketNodeViewModel
│   │   └── confidenceExplain.vm.ts    ← ConfidenceExplainViewModel
│   └── builders/
│       ├── groupStage.builder.ts
│       └── knockout.builder.ts
├── app/tournament/
│   └── page.tsx                     ← 路由页面（空壳）
└── components/
    ├── ui/                          ← shadcn/ui 基础组件
    ├── business/                     ← 业务组件（空壳）
    │   ├── MatchCard.tsx
    │   ├── ChampionPath.tsx
    │   └── BracketNode.tsx
    └── presentation/                  ← 展示组件（空壳）
        └── TournamentPresentation.tsx
```

**验收标准**：
- [ ] `latest-json.types.ts` 完整覆盖 latest.json 字段
- [ ] `loader.ts` 能读取 latest.json
- [ ] 所有 ViewModel 存在（.vm.ts）且类型正确
- [ ] `app/tournament/page.tsx` 路由正确
- [ ] `business/` 组件有骨架代码（`// TODO` 即可）
- [ ] 无新 JSON 文件生成

**TP-1 风险控制**：
- 只做 TypeScript 类型 + 空组件
- 不写任何 UI 样式
- 不写任何动画
- 不连接任何 API（loader 直接 import JSON）

---

### TP-2：Narrative Layer（约 2 小时）

**目标**：Champion Story + Confidence Explain + Reasoning 引用

**交付物**：
```
frontend/src/lib/tournament/
└── builders/
    └── championNarrative.builder.ts   ← Story Timeline Builder

frontend/src/components/
├── business/
│   ├── MatchCard.tsx                 ← 完成 MatchCardViewModel 消费
│   ├── ChampionPath.tsx              ← 完成 ChampionPathViewModel 消费
│   └── BracketNode.tsx              ← 完成 BracketNodeViewModel 消费
└── presentation/
    ├── ChampionJourney.tsx           ← Story Timeline 展示
    ├── ConfidenceExplain.tsx          ← 置信度解释面板
    └── ReasoningQuote.tsx             ← Reasoning 引用卡片
```

**验收标准**：
- [ ] Champion Journey 有 Group→R16→QF→SF→Final 叙事
- [ ] 叙事引用已有 reasoning，不生成新文本
- [ ] Confidence Explain 点击展开（数据来自 factors）
- [ ] Reasoning Quote 标注来源（group_prediction_tool 等）

**TP-2 风险控制**：
- Narrative 文本必须全部来自 latest.json
- 不调用 LLM 生成文本
- 不修改 ViewModel 类型

---

### TP-3：Interactive Experience（约 4 小时）

**目标**：Bracket 交互 + 动画 + Replay Prediction + Responsive

**交付物**：
```
frontend/src/components/
├── business/
│   └── BracketView.tsx               ← 完成赛程树
├── presentation/
│   ├── TournamentPresentation.tsx     ← 完成总展示
│   └── ReplayPrediction.tsx          ← 20秒自动播放动画
└── app/tournament/
    └── page.tsx                     ← 接入数据，完成页面
```

**新增功能**：
- Bracket 节点 Hover/Click 展开 Prediction/Factors/Reasoning
- Replay Prediction 动画（Group→R16→QF→SF→Final，20秒）
- Framer Motion 动画
- Mobile Responsive

**验收标准**：
- [ ] 赛程树展示 R16→QF→SF→Final
- [ ] 每个节点可展开（Prediction + Factors + Reasoning）
- [ ] Replay Prediction 有 20 秒动画
- [ ] Mobile 端可用（375px / 768px / 1280px）
- [ ] Lighthouse Performance > 90

**TP-3 风险控制**：
- 动画优先 Framer Motion，不自己写 CSS 动画
- Mobile First，但不放弃 Desktop 体验
- 动画时间不超过 30 秒（评委注意力有限）

---

## 五、Champion Story Timeline（重设计）

### 5.1 Story Timeline 展示

CTO 要求将 Champion Narrative 改为 Story Timeline，按 Group Stage → R16 → QF → SF → Final 叙事。

```
┌─────────────────────────────────────────────────────────────┐
│  🏆 Champion Journey                                         │
│  Argentina · 100.0%                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🟢 GROUP STAGE                                            │
│  ─────────────────                                          │
│  AI predicted Argentina to top Group A                      │
│  Confidence 91%                                             │
│  "Argentina（强队，实力72.3）主场优势明显"                   │
│                                                             │
│  ↓                                                         │
│                                                             │
│  🟢 ROUND OF 16                                           │
│  ────────────────────────                                    │
│  Argentina advanced with 78% probability                      │
│  vs Netherlands                                             │
│  "ELO评分差185分，差距显著"                                 │
│                                                             │
│  ↓                                                         │
│                                                             │
│  🟡 QUARTER FINAL                                          │
│  ────────────────────                                       │
│  ELO advantage + attacking efficiency                        │
│  vs England · 59.1%                                         │
│  "England（强队，实力66.5）主场优势明显"                     │
│                                                             │
│  ↓                                                         │
│                                                             │
│  🟡 SEMI FINAL                                             │
│  ─────────────────                                          │
│  Monte Carlo simulation favored Argentina                    │
│  vs Brazil · 49.6%                                         │
│  "Brazil（强队，实力71.8）主场优势明显"                      │
│                                                             │
│  ↓                                                         │
│                                                             │
│  🔵 FINAL                                                  │
│  ───────                                                    │
│  Champion Probability reached 87%                           │
│  vs France · 49.6%                                          │
│  "France（强队，实力70.2）主场优势明显"                      │
│                                                             │
│  ↓                                                         │
│                                                             │
│  🏆 CHAMPION                                               │
│  ──────────                                                 │
│  Argentina                                                 │
│  Monte Carlo: 10,000 iterations · 66m 28s                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**关键约束**：
- ❌ 无 "Beat" / "Wins" 等动词（比分不可信）
- ✅ 全部引用已有 reasoning
- ✅ 按 Group→R16→QF→SF→Final 叙事
- ✅ 标注 Confidence Level（🟢高 / 🟡中 / 🟣低）

---

### 5.2 AI Prediction Confidence Explain

点击置信度分数展开解释：

```
┌─────────────────────────────────────────────────────────────┐
│  Prediction Confidence                                      │
│                                                             │
│      87                                                    │
│      High                                                  │
│                                                             │
│  Why is it High?                                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  ✓ ELO difference significant                      │  │
│  │    Home Elo 2151 vs Away Elo 1943 (diff +208)      │  │
│  │                                                     │  │
│  │  ✓ Recent form stable                              │  │
│  │    Last 10 A-matches: 7W 2D 1L                   │  │
│  │                                                     │  │
│  │  ✓ Historical matchup advantage                   │  │
│  │    3 wins in last 5 encounters                    │  │
│  │                                                     │  │
│  │  ✓ Simulation convergence reached                   │  │
│  │    Monte Carlo 10,000 iterations                   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**数据来源**（全部来自 latest.json）：
- ELO difference → factor.elo_diff
- Recent form → factor.recent_form（如果可用）
- Historical matchup → factor.*（任一因子）
- Monte Carlo convergence → reasoning_chain

---

### 5.3 Bracket 节点交互设计

每个节点 Hover/Click 展开：

```
┌─────────────────────┐
│  Argentina          │
│  72%               │
│  [Hover / Click]    │
└─────────────────────┘
         ↓ Hover/Click
┌─────────────────────────────────────────────────────────────┐
│  Prediction                                                    │
│  ───────────                                                   │
│  Home Win 72% · Draw 15% · Away Win 13%                      │
│                                                             │
│  Confidence                                                   │
│  ───────────                                                  │
│  87 · High                                                  │
│  [Why is it High? ▼]                                        │
│                                                             │
│  Factors                                                     │
│  ───────                                                     │
│  ELO Rating Advantage          ↑ 42%                        │
│  FIFA World Ranking Adv         ↑ 26%                        │
│                                                             │
│  Reasoning                                                   │
│  ─────────                                                   │
│  "Argentina（强队，实力72.3）主场优势明显，                    │
│   ELO评分差185分，差距显著"                                   │
│   — source: group_prediction_tool                            │
│                                                             │
│  Snapshot                                                    │
│  ─────────                                                   │
│  snap_2026_07_04 · v20260704_1008                         │
└─────────────────────────────────────────────────────────────┘
```

---

### 5.4 Replay Prediction 播放器（TP-3 新功能）

播放器控制（不是固定 20 秒）：

```
┌─────────────────────────────────────────────────────────────┐
│  ▶ Play                    ━━━━━━━━━━●━━━━━━━━━  0:12  │
│                                                              │
│  [▶] [⏸] [↺]       0.5×    1×    2×                    │
└─────────────────────────────────────────────────────────────┘
```

**播放器控制**：
- Play / Pause / Restart
- Progress Bar（可拖动）
- Playback Speed：0.5× / 1× / 2×
- Current Time 显示

**时间轴（可配置）**：
| Speed | Total Duration |
|---|---|
| 0.5× | 40s |
| 1× | 20s |
| 2× | 10s |

**动画分段**：
```
0s-4s   → Group Stage 高亮
4s-8s   → R16 展开 + Champion 路径点亮
8s-12s  → QF 展开
12s-16s → SF 展开
16s-20s → Final + Champion 展示
```

**动画类型**：
- 逐节点点亮（Framer Motion `whileHover`）
- 连线动画（SVG `pathLength`）
- Champion 脉冲动画（`scale` + `boxShadow`）

---

## 六、数据流（无新文件）

```
latest.json（唯一数据源）
       │
       │ fetch (via Next.js / public/data/latest.json)
       │
       ▼
TournamentViewModel（TypeScript，仅内存中）
       │
       ├── getGroupStage()       → GroupStageView
       ├── getKnockoutBracket()  → KnockoutBracketView
       ├── getChampionPath()     → ChampionPathView
       └── getMonteCarloStats()  → MonteCarloStatsView
       │
       ▼
React Components
       │
       ├── BracketView
       ├── ChampionPathPanel
       ├── GroupStageCard
       └── ReasoningQuote
       │
       ▼
用户看到
```

---

## 七、与旧方案的对比

| 维度 | 旧方案（TE） | 新方案（TP） |
|---|---|---|
| **新增文件** | tournament_engine.json | 无 |
| **新增引擎** | tournament_engine.py | 无（用 ViewModel 替代） |
| ** Reasoning 来源** | 重新生成 | 引用已有 |
| **关联方式** | 时间戳 | MatchID |
| **Champion Path** | 有比分（2-1） | 无比分（只有胜率） |
| **Monte Carlo** | 重新运行 | 引用已有统计 |
| **数据源** | latest.json + tournament_engine.json | latest.json（唯一） |

---

## 八、Backend Freeze 最终确认

```
❌ 禁止修改 worldcup_agent/prediction/agent.py
❌ 禁止修改 worldcup_agent/prediction/prediction_schema.py
❌ 禁止修改 worldcup_agent/prediction/elo_system.py
❌ 禁止修改 data/snapshots/latest.json（仅读取）

❌ 不新增 tournament_engine.json（新数据文件）
❌ 不新增 tournament_engine.py（新预测引擎）
❌ 不重新生成 reasoning（hallucination）

✅ 允许新增 frontend/src/（整个前端工程）
✅ 允许新增 frontend/src/lib/tournament/types/
✅ 允许新增 frontend/src/lib/tournament/loader.ts
✅ 允许新增 frontend/src/lib/tournament/viewModels/*.vm.ts
✅ 允许新增 frontend/src/lib/tournament/builders/*.builder.ts
✅ 允许新增 frontend/src/components/business/*.tsx
✅ 允许新增 frontend/src/components/presentation/*.tsx
✅ 允许新增 frontend/src/app/tournament/page.tsx
```

---

## 六、组件分层架构（UI Adapter Pattern）

### 6.1 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer（展示层）                                │
│  ├── TournamentPresentation.tsx   ← 整页展示容器           │
│  ├── ChampionJourney.tsx           ← Story Timeline         │
│  └── ReplayPrediction.tsx          ← 播放动画               │
├─────────────────────────────────────────────────────────────┤
│  Business Layer（业务层）                                   │
│  ├── MatchCard.tsx                ← 消费 MatchCardViewModel  │
│  ├── ChampionPath.tsx             ← 消费 ChampionPathViewModel│
│  └── BracketNode.tsx             ← 消费 BracketNodeViewModel  │
├─────────────────────────────────────────────────────────────┤
│  UI Layer（基础层）                                        │
│  ├── shadcn/ui                    ← Button, Card, Badge     │
│  ├── Lucide React                 ← Icons                  │
│  └── Tailwind                    ← Styling                │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 目录结构

```
frontend/src/
├── app/
│   ├── page.tsx                   ← Home
│   ├── match/[id]/page.tsx        ← Match
│   └── tournament/
│       └── page.tsx                ← Tournament（路由）
├── components/
│   ├── ui/                        ← shadcn/ui 基础组件
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── separator.tsx
│   │   └── skeleton.tsx
│   ├── business/                  ← 业务组件（消费 ViewModel）
│   │   ├── MatchCard.tsx         ← MatchCardViewModel → UI
│   │   ├── ChampionPath.tsx       ← ChampionPathViewModel → UI
│   │   ├── BracketNode.tsx        ← BracketNodeViewModel → UI
│   │   ├── BracketView.tsx        ← BracketViewModel → UI
│   │   ├── ConfidenceExplain.tsx  ← ConfidenceExplainViewModel → UI
│   │   └── ReasoningQuote.tsx     ← reasoning → UI
│   └── presentation/              ← 展示组件（组合 business）
│       ├── TournamentPresentation.tsx  ← 整页容器
│       ├── ChampionJourney.tsx         ← Story Timeline
│       └── ReplayPrediction.tsx        ← 播放动画
└── lib/
    └── tournament/                ← ViewModel + Data Layer
        ├── types/
        │   ├── latest-json.types.ts
        │   └── ui-adapter.types.ts
        ├── loader.ts
        ├── viewModels/
        │   ├── matchCard.vm.ts
        │   ├── championPath.vm.ts
        │   ├── bracketNode.vm.ts
        │   └── confidenceExplain.vm.ts
        └── builders/
            ├── groupStage.builder.ts
            ├── knockout.builder.ts
            └── championNarrative.builder.ts
```

### 6.3 组件职责

| 层级 | 组件 | 职责 |
|---|---|---|
| **Presentation** | `TournamentPresentation` | 整页布局，数据组合 |
| **Presentation** | `ChampionJourney` | Story Timeline 展示 |
| **Presentation** | `ReplayPrediction` | 20 秒播放动画 |
| **Business** | `MatchCard` | 消费 `MatchCardViewModel`，渲染比赛卡片 |
| **Business** | `ChampionPath` | 消费 `ChampionPathViewModel`，渲染路径 |
| **Business** | `BracketNode` | 消费 `BracketNodeViewModel`，渲染节点 |
| **Business** | `ConfidenceExplain` | 消费 `ConfidenceExplainViewModel`，渲染解释 |
| **Business** | `ReasoningQuote` | 引用 `reasoning`，渲染引用样式 |
| **UI** | `Card`, `Badge`, `Button` | shadcn/ui 基础组件 |

---

## 七、Backend Freeze 最终确认

### 9.1 比赛要求 vs TP 方案

| 要求 | TP 方案实现方式 | 状态 |
|---|---|---|
| **逐轮预测结果** | ViewModel 读取 knockout_predictions.rounds{}，展示 R16→QF→SF→Final | ✅ |
| **推理依据** | ViewModel 引用每场比赛的 reasoning 字段，不生成新文本 | ✅ |
| **完整冠军路径** | ChampionPathView 按 MatchID 回溯 4 legs，无比分，只有胜率 | ✅ |
| **Monte Carlo 统计** | 引用 reasoning_chain 中 monte_carlo_tool.duration_ms | ✅ |

### 9.2 评委体验

| 评委问题 | TP 方案回答方式 |
|---|---|
| "Argentina 怎么一步步打上去的？" | ChampionPathPanel 展示 4 个 legs + reasoning |
| "AI 为什么预测 Argentina 赢？" | ReasoningQuote 引用已有 reasoning 文本 |
| "Monte Carlo 跑了多少次？" | MonteCarloStats 展示 10000 次 + 耗时 |
| "这个 reasoning 是真的吗？" | 直接引用 latest.json.reasoning_chain，不重新生成 |
| "比分是多少？" | **不展示比分**（比分是占位，不代表真实预测） |

---

## 十一、TP 最终执行路径（锁定）

```
TP Design（Tournament Presentation 设计）
    ↓ 本文档完成
    ↓ CTO 批准通过

─────────────────────────────────────────────────────────────

TP-1：Frontend Foundation（约 2 小时）
├── Types（latest-json.types.ts + ui-adapter.types.ts）
├── Data Loader（loader.ts）
├── ViewModels（matchCard.vm.ts 等）
├── Business Skeleton（MatchCard.tsx 等，空壳）
├── Presentation Skeleton（TournamentPresentation.tsx 等）
├── Route（app/tournament/page.tsx）
└── Git commit

─────────────────────────────────────────────────────────────

TP-2：Narrative Layer（约 2 小时）
├── ChampionJourney.tsx（Story Timeline）
├── ConfidenceExplain.tsx（置信度解释）
├── ReasoningQuote.tsx（引用卡片）
└── Git commit

─────────────────────────────────────────────────────────────

TP-3：Interactive Experience（约 4 小时）
├── BracketView.tsx（赛程树）
├── BracketNode 交互（Hover/Click 展开）
├── ReplayPrediction.tsx（20 秒动画）
├── Framer Motion 动画
├── Mobile Responsive
└── Git commit + Deploy to Vercel

─────────────────────────────────────────────────────────────

Post-Sprint
├── Home Page + Tournament Page 合并
├── 统一数据消费层
├── 统一设计语言
└── 评委 Demo 验收
```

---

## 十二、文档体系锁定声明

```
本文档体系已完整，无需新增任何设计文档：

✅ FRONTEND_ARCHITECTURE.md  — 架构设计
✅ PRODUCT_SPEC.md            — 产品规格
✅ TOURNAMENT_ENGINE_DESIGN.md — Tournament Presentation 设计（v3）

下一步：
  全部进入代码实现阶段。
  严格执行 TP-1 → TP-2 → TP-3 → Deployment。
```
