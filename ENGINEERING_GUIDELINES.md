# Engineering Guidelines
**Author**: Cursor AI (Qoder) · **Date**: 2026-07-05
**Status**: LOCKED — 本文档为工程规范，非设计文档，后续仅修复 typo，禁止新增章节
**Version**: v2.0 — 2026-07-05 升级，新增核心规则

---

## 元声明

- 本文档为**工程规范**，不是设计文档
- 本文档为 **LOCKED** 状态，仅允许修复 typo
- 新增内容必须通过 Pull Request + Code Review
- 本文档禁止作为"新增功能的讨论场所"
- **所有规则按 P0（必须）/ P1（建议）/ P2（后期）分类**

---

## 元声明

- 本文档为**工程规范**，不是设计文档
- 本文档为 **LOCKED** 状态，仅允许修复 typo
- 新增内容必须通过 Pull Request + Code Review
- 本文档禁止作为"新增功能的讨论场所"

---

## 核心原则

每次代码评审，必须回答三个问题：

### Q1: 后端适配性
> 如果后端把 `latest.json` 换成 FastAPI，这个页面需要改多少代码？

**越少越好**。Adapter Layer 必须能隔离数据源变更。

### Q2: 组件复用性
> 如果比赛增加"最佳射手预测"模块，能否复用现有组件？

**复用率越高越好**。ViewModel 必须语义化，组件必须无状态。

### Q3: 评委第一印象
> 评委第一次打开网站，10 秒内能否理解"这是一个每天更新、可解释的世界杯 AI Agent"？

**越直观越好**。UI 必须有产品感，reasoning 必须可见。

---

## 核心规则 #0：Presentation Never Thinks ⭐

> **P0 - 绝对禁止，前端永远只展示，不推理**

这是本项目最重要的规则，适用于所有比赛项目。

```typescript
// ❌ 禁止：前端重新计算预测结果
const myProbability = calculateWinProbability(homeTeam, awayTeam);
const myChampion = predictChampion(groupStandings);
const myRanking = rankTeams(eloRatings);

// ✅ 必须：前端只展示后端计算好的数据
const championProbability = snapshot.champion_probability;
const reasoning = match.reasoning;
```

### 允许做的事

```typescript
// ✅ 排序（仅展示排序）
const sortedMatches = [...matches].sort((a, b) => b.confidence - a.confidence);

// ✅ 格式化
const percentage = (prob * 100).toFixed(1) + "%";
const date = new Date(isoString).toLocaleDateString();

// ✅ 颜色映射
const confidenceColor = level === "High" ? "green" : "yellow";

// ✅ 动画
<motion.div animate={{ opacity: 1 }} />
```

### 禁止做的事

```typescript
// ❌ 禁止：重新预测
const predictedWinner = homeProb > awayProb ? home : away;

// ❌ 禁止：重新排名
const newRanking = teams.sort((a, b) => b.elo - a.elo);

// ❌ 禁止：重新生成推理
const generatedReasoning = generateReasoning(match);

// ❌ 禁止：Monte Carlo 计算
const champion = runMonteCarlo(teams, iterations);
```

### 原因

如果前端开始自行推导：
- 后端：阿根廷 80%
- 前端：阿根廷 75%

**评委会认为 Agent 不一致，直接扣分**。

---

## 核心规则 #1：Adapter 纯映射原则

> **P0 - Adapter 只做 A→B，不做 A→计算→B**

### Adapter 限制

```typescript
// ❌ 禁止：Adapter 出现 if/else 超过两层
export class SnapshotAdapter {
  static fromJson(snapshot: Snapshot): AdapterOutput {
    // 禁止超过两层的条件判断
    if (value >= 70) {
      level = "High";
      if (probAvg < 0.3) {  // ❌ 第二层
        status = "warn";
      }
    }
  }
}

// ✅ 正确：纯映射，无业务逻辑
export class SnapshotAdapter {
  static fromJson(snapshot: Snapshot): AdapterOutput {
    return {
      champion: snapshot.champion,
      championProbability: snapshot.champion_probability,
      // 纯映射，不计算
    };
  }
}
```

### Adapter 永远只负责

```text
latest.json → 中间格式
```

不能：
- 排序
- 过滤
- 计算
- 推导
- Monte Carlo
- 排名

### 业务逻辑放哪里

```text
Loader → Adapter → ViewModel → React
                       ↑
              业务逻辑在这里
```

---

## 核心规则 #2：ViewModel 单一职责原则

> **P0 - 每个 ViewModel 只负责一个 Component，不超过 200 行**

### 禁止的模式

```typescript
// ❌ 禁止：TournamentVM 800 行
// 一个文件包含 Champion、Group、Timeline、Bracket...
export class TournamentVM {
  buildChampion() { ... }
  buildGroup() { ... }
  buildTimeline() { ... }
  buildBracket() { ... }
}
```

### 正确的模式

```text
MatchCard.vm.ts      → 40 行 → MatchCard 组件
ChampionPath.vm.ts   → 60 行 → ChampionPath 组件
BracketNode.vm.ts    → 50 行 → BracketNode 组件
Confidence.vm.ts     → 40 行 → ConfidenceExplain 组件
```

### 每个 VM 的职责

```typescript
// ✅ MatchCardViewModel 只负责 MatchCard 的展示数据
export interface MatchCardViewModel {
  title: string;        // "Argentina vs Brazil"
  subtitle: string;     // "Group Stage - Match 12"
  kickoff: string;      // "2026-06-15 20:00"
  prediction: { ... };  // 预测数据（来自后端）
  confidence: { ... };  // 置信度（来自后端）
}
```

### ViewModel UI 化原则

```typescript
// ❌ 错误：ViewModel 是数据模型
interface MatchVM {
  elo: number;
  group: string;
  matches: Match[];
}

// ✅ 正确：ViewModel 是 UI 模型
interface MatchCardViewModel {
  title: string;      // UI 显示用
  subtitle: string;   // UI 显示用
  progress: string;  // UI 显示用 "8/10 teams decided"
  badge: string;     // UI 显示用 "High Confidence"
  icon: string;      // UI 显示用 "Trophy"
}
```

---

## 核心规则 #3：Snapshot 隐藏原则

> **P0 - 只有 Loader 知道 Snapshot 类型，其他层不知道**

### 依赖方向

```text
Snapshot（原始数据）
    ↓
Loader（唯一知道 Snapshot 的地方）
    ↓
Adapter（转换为中间格式）
    ↓
ViewModel（消费中间格式）
    ↓
React（只消费 ViewModel）
```

### 禁止的模式

```tsx
// ❌ 禁止：React 组件直接导入 Snapshot 类型
import type { Snapshot } from "@/lib/tournament/types";

// ❌ 禁止：ViewModel 导出 Snapshot 相关类型
export type { Snapshot } from "@/lib/tournament/types";
```

### 允许的模式

```tsx
// ✅ 正确：组件只导入 ViewModel
import type { MatchCardViewModel } from "@/lib/tournament/types";

export function MatchCard({ vm }: MatchCardProps) {
  // vm 是 MatchCardViewModel，不是 Snapshot
}
```

---

## 核心规则 #4：类型文件精简原则

> **P1 - 永远只有两类类型文件**

### 禁止的模式

```text
// ❌ 禁止：类型文件越来越多
types/
├── match.types.ts
├── group.types.ts
├── snapshot.types.ts
├── vm.types.ts
├── ui.types.ts
├── common.types.ts
├── api.types.ts
└── index.ts  // 导出全部
```

### 正确的模式

```text
lib/tournament/types/
├── index.ts              ← 统一导出
├── latest-json.types.ts ← Domain Types（对应 latest.json）
└── ui-adapter.types.ts  ← UI Types（ViewModel 类型）
```

### 类型文件职责

```typescript
// latest-json.types.ts — Domain Types
// 与 latest.json 一一对应，修改需谨慎
export interface Snapshot { ... }
export interface GroupMatch { ... }

// ui-adapter.types.ts — UI Types
// ViewModel 类型，供 React 使用
export interface MatchCardViewModel { ... }
export interface ChampionPathViewModel { ... }
```

---

## 核心规则 #5：VM 不调 Adapter 原则

> **P1 - 依赖方向必须单向：Loader → Adapter → VM Factory → React**

### 依赖方向检查

```text
✅ 正确：
Loader → Adapter → VM → Component

❌ 错误：
VM → Adapter（循环依赖风险）
Component → Adapter（违反分层）
```

### 依赖注入模式

```typescript
// ❌ 禁止：VM 直接调用 Adapter
export class MatchCardVMBuilder {
  static build(snapshot: Snapshot, matchId: string) {
    const adapter = SnapshotAdapter.fromJson(snapshot); // ❌ VM 知道 Adapter
  }
}

// ✅ 正确：使用依赖注入
export class MatchCardVMBuilder {
  constructor(private adapter: SnapshotAdapter) {}
  build(snapshot: Snapshot, matchId: string) {
    // 使用注入的 adapter
  }
}

// ✅ 更推荐：数据在 Hook 层处理
export function useMatchCard(matchId: string): MatchCardViewModel {
  const snapshot = useSnapshot();
  const adapter = useAdapter(); // Hook 提供
  return adapter.toMatchCardVM(snapshot, matchId);
}
```

---

## 一、目录规范

## 一、目录规范

```
frontend/src/
│
├── app/                          ← Next.js App Router
│   ├── layout.tsx                ← Root Layout + Nav
│   ├── page.tsx                  ← Home
│   ├── match/
│   │   └── [id]/
│   │       └── page.tsx         ← Match Detail
│   ├── tournament/
│   │   └── page.tsx            ← Tournament
│   ├── compare/
│   │   └── page.tsx            ← Compare（Optional）
│   └── about/
│       └── page.tsx             ← About
│
├── components/
│   ├── ui/                      ← shadcn/ui 基础组件
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── separator.tsx
│   │   ├── skeleton.tsx
│   │   ├── tooltip.tsx
│   │   └── progress.tsx
│   │
│   ├── business/                ← 业务组件（消费 ViewModel）
│   │   ├── MatchCard.tsx       ← 消费 MatchCardViewModel
│   │   ├── ChampionPath.tsx     ← 消费 ChampionPathViewModel
│   │   ├── BracketNode.tsx     ← 消费 BracketNodeViewModel
│   │   ├── BracketView.tsx     ← 消费 BracketViewModel
│   │   ├── ConfidenceExplain.tsx ← 消费 ConfidenceExplainViewModel
│   │   ├── ReasoningQuote.tsx   ← 引用 reasoning
│   │   ├── GroupStageCard.tsx  ← 消费 GroupStageViewModel
│   │   └── StandingsTable.tsx   ← 消费 StandingsViewModel
│   │
│   └── presentation/             ← 展示组件（组合 business）
│       ├── TournamentPresentation.tsx ← 整页容器
│       ├── ChampionJourney.tsx       ← Story Timeline
│       └── ReplayPrediction.tsx       ← 播放动画
│
├── lib/
│   ├── tournament/
│   │   ├── types/
│   │   │   ├── latest-json.types.ts   ← latest.json 原始类型
│   │   │   └── ui-adapter.types.ts    ← UI Adapter 类型
│   │   ├── loader/
│   │   │   └── snapshot.loader.ts      ← JSON Loader + Adapter
│   │   ├── adapters/
│   │   │   └── snapshot.adapter.ts    ← Adapter Layer（可选）
│   │   ├── viewModels/
│   │   │   ├── matchCard.vm.ts
│   │   │   ├── championPath.vm.ts
│   │   │   ├── bracketNode.vm.ts
│   │   │   ├── bracket.vm.ts
│   │   │   ├── confidenceExplain.vm.ts
│   │   │   └── groupStage.vm.ts
│   │   └── builders/
│   │       ├── groupStage.builder.ts
│   │       ├── knockout.builder.ts
│   │       └── championNarrative.builder.ts
│   │
│   ├── utils.ts                 ← 通用工具
│   └── cn.ts                    ← className 合并（clsx + tailwind-merge）
│
├── hooks/                       ← 自定义 Hooks
│   ├── useSnapshot.ts          ← Snapshot 数据 Hook
│   ├── useTournament.ts        ← Tournament 数据 Hook
│   └── useMatch.ts             ← Match 数据 Hook
│
├── constants/                   ← 常量
│   ├── colors.ts               ← Color Token
│   ├── stages.ts               ← Stage 定义
│   └── config.ts               ← App Config
│
└── styles/
    └── globals.css             ← Tailwind + CSS Variables
```

---

## 二、组件规范

### 2.1 组件分层规则

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer（展示层）                                │
│  职责：布局、数据组合、动画                                 │
│  规则：只组合 business 组件，不直接消费 ViewModel           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Business Layer（业务层）                                   │
│  职责：消费 ViewModel，渲染 UI                             │
│  规则：只消费 props，不自己读数据，不自己 fetch             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  UI Layer（基础层）                                        │
│  职责：原子组件，无业务逻辑                                │
│  规则：shadcn/ui，禁止修改                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Business Component 模板

```tsx
// ❌ 错误：组件自己读数据
export function MatchCard({ matchId }: { matchId: string }) {
  const data = useSnapshot(); // ❌ 禁止在组件内部 fetch
  return <div>{data.matches[matchId].home_team}</div>;
}

// ✅ 正确：组件只消费 ViewModel
export function MatchCard({ vm }: { vm: MatchCardViewModel }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{vm.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <WinProbabilityBar {...vm.prediction} />
        <ConfidenceBadge level={vm.confidence.level} />
      </CardContent>
    </Card>
  );
}
```

### 2.3 Props 传递规则

```tsx
// ❌ 错误：传递原始数据
<MatchCard
  home_team="Argentina"
  away_team="Mexico"
  home_win_prob={0.588}
  reason="Argentina 主场优势明显"
/>

// ✅ 正确：传递 ViewModel
<MatchCard vm={matchCardViewModel} />
```

### 2.4 无状态规则

```tsx
// ❌ 错误：组件内部有状态（业务逻辑）
function MatchCard({ matchId }) {
  const [expanded, setExpanded] = useState(false);
  const { data } = useSnapshot();
  // ...
}

// ✅ 正确：组件无状态，状态由 Hook 或父组件管理
function MatchCard({ vm, onExpand }: { vm: MatchCardViewModel; onExpand?: () => void }) {
  return (
    <Card>
      <button onClick={onExpand}>Expand</button>
    </Card>
  );
}
```

---

## 三、数据流规范

### 3.1 四层数据流

```
┌─────────────────────────────────────────────────────────────┐
│  Data Source（数据源）                                       │
│  latest.json / FastAPI / Mock Data                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Loader（加载器）                                           │
│  snapshot.loader.ts — 读取数据，类型检查                   │
│  职责：fetch + parse + validate                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Adapter（适配器，可选）                                     │
│  snapshot.adapter.ts — 数据格式转换                        │
│  职责：latest.json → 中间格式（未来 FastAPI 可用）       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  ViewModel（视图模型）                                       │
│  *.vm.ts — UI Adapter，消费原始数据，生成 UI 模型         │
│  职责：语义化、格式化、组合                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  UI Components（UI 组件）                                   │
│  business/*.tsx — 消费 ViewModel，渲染                    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Adapter Layer 说明

```typescript
// snapshot.adapter.ts
// 如果未来切换到 FastAPI，只需修改这里
// ViewModel 和 UI 不需要改动

export interface SnapshotData {
  // 中间格式（稳定契约）
  champion: string;
  groups: GroupData[];
  knockout: KnockoutData;
  reasoningChain: ReasoningStep[];
}

export class SnapshotAdapter {
  // latest.json → 中间格式
  static fromJson(json: LatestJson): SnapshotData { ... }

  // Future: FastAPI Response → 中间格式
  static fromApi(response: ApiResponse): SnapshotData { ... }
}
```

### 3.3 Hooks 规范

```typescript
// hooks/useSnapshot.ts
// 组件通过 Hook 获取 ViewModel，不是直接 import Loader

export function useSnapshot(): MatchCardViewModel | null {
  const { data } = useSWR("snapshot", fetcher);

  if (!data) return null;

  // 在 Hook 内构建 ViewModel，不在组件内构建
  return buildMatchCardViewModel(data);
}
```

---

## 四、Animation 规范

### 4.1 统一使用 Framer Motion

```tsx
// ❌ 禁止：CSS Animation
.card {
  animation: fadeIn 0.3s ease;
}

// ✅ 必须：Framer Motion
import { motion } from "framer-motion";

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3, ease: "easeOut" }}
>
  {children}
</motion.div>
```

### 4.2 Animation 变量

```typescript
// constants/animations.ts
export const ANIMATIONS = {
  // 页面切换
  page: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3 },
  },
  // 卡片展开
  expand: {
    initial: { height: 0, opacity: 0 },
    animate: { height: "auto", opacity: 1 },
    transition: { duration: 0.2 },
  },
  // 节点点亮
  highlight: {
    scale: 1.05,
    boxShadow: "0 0 20px var(--accent)",
    transition: { duration: 0.3 },
  },
  // 路径连线
  path: {
    pathLength: [0, 1],
    transition: { duration: 0.5 },
  },
};
```

### 4.3 Replay Prediction 播放器

```tsx
// 播放器控制
interface ReplayControls {
  isPlaying: boolean;
  currentTime: number;      // 0-20（秒）
  duration: number;         // 20（秒）
  playbackRate: 0.5 | 1 | 2;

  play(): void;
  pause(): void;
  restart(): void;
  seek(time: number): void;
  setPlaybackRate(rate: 0.5 | 1 | 2): void;
}
```

---

## 五、Color Token 规范

### 5.1 CSS Variables

```css
/* globals.css */
:root {
  /* 背景 */
  --bg: #0a0e14;
  --surface: #131a24;
  --surface2: #1a2333;
  --border: #1e2a3a;

  /* 文本 */
  --text: #cdd9e5;
  --muted: #768390;

  /* 强调色 */
  --accent: #58a6ff;
  --green: #3fb950;   /* 高可信 / 主胜 */
  --yellow: #d29922;  /* 中可信 / 平局 */
  --red: #f85149;     /* 低可信 / 客胜 */
  --orange: #e8854a;  /* 客胜备选 */
  --purple: #bc8cff;   /* 特殊状态 */

  /* Typography */
  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  /* Spacing */
  --radius: 0.75rem;  /* 12px */
  --radius-sm: 0.5rem;
  --radius-lg: 1rem;
}
```

### 5.2 Tailwind Config

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        surface2: "var(--surface2)",
        border: "var(--border)",
        text: "var(--text)",
        muted: "var(--muted)",
        accent: "var(--accent)",
        green: "var(--green)",
        yellow: "var(--yellow)",
        red: "var(--red)",
        orange: "var(--orange)",
        purple: "var(--purple)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        DEFAULT: "var(--radius)",
        sm: "var(--radius-sm)",
        lg: "var(--radius-lg)",
      },
    },
  },
};
```

### 5.3 使用规则

```tsx
// ❌ 禁止：硬编码颜色
<div className="bg-[#0a0e14] text-[#cdd9e5]">

// ✅ 必须：使用 CSS Variable
<div className="bg-bg text-text">

// ✅ 正确：使用 Tailwind Token
<div className="bg-surface border-border text-muted">
```

---

## 六、Icon 规范

### 6.1 统一使用 Lucide React

```tsx
// ❌ 禁止：混用多个 Icon 库
import { HeartIcon } from "@heroicons/react";      // ❌
import { FcRating } from "react-icons/fc";         // ❌

// ✅ 必须：统一 Lucide React
import { Trophy, TrendingUp, Brain, Activity } from "lucide-react";
```

### 6.2 Icon 命名规则

```tsx
// ❌ 错误：语义不清晰
<HeartIcon size={16} />

// ✅ 正确：语义清晰
<Trophy className="w-4 h-4 text-yellow" />   // 冠军
<TrendingUp className="w-4 h-4 text-green" /> // 趋势
<Brain className="w-4 h-4 text-accent" />    // AI/推理
```

### 6.3 常用 Icon 映射

```typescript
// constants/icons.ts
export const ICONS = {
  // 状态
  trophy: Trophy,          // 🏆 冠军
  medal: Medal,             // 🥇 奖牌
  star: Star,               // ⭐ 亮点
  check: CheckCircle,        // ✅ 完成
  clock: Clock,             // 🕐 时间

  // AI / 推理
  brain: Brain,             // 🧠 AI 分析
  sparkles: Sparkles,        // ✨ AI 生成
  activity: Activity,        // 📊 活跃度

  // 比赛
  users: Users,             // 👥 球队
  target: Target,           // 🎯 预测
  trending: TrendingUp,      // 📈 趋势

  // 导航
  home: Home,               // 🏠 首页
  bracket: GitBranch,       // 🔀 赛程树
  compare: ArrowLeftRight,  // ⚖️ 对比

  // 控制
  play: Play,               // ▶️ 播放
  pause: Pause,             // ⏸️ 暂停
  restart: RotateCcw,       // ↺ 重播
  expand: Maximize2,         // ↗ 展开
};
```

---

## 七、Accessibility 规范

### 7.1 键盘导航

```tsx
// ❌ 禁止：只能鼠标交互
<button onClick={onClick}>Expand</button>

// ✅ 必须：支持键盘
<button
  onClick={onClick}
  onKeyDown={(e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick();
    }
  }}
  tabIndex={0}
  role="button"
  aria-expanded={isExpanded}
>
  Expand
</button>
```

### 7.2 Bracket 节点交互

```tsx
// BracketNode 必须支持 Tab + Enter 展开
<motion.div
  tabIndex={0}
  role="button"
  aria-label={`${team} ${winProb}% - Press Enter to expand details`}
  onKeyDown={(e) => {
    if (e.key === "Enter") toggleExpanded();
    if (e.key === "Escape") setExpanded(false);
  }}
>
```

### 7.3 Focus Visible

```css
/* globals.css */
*:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

---

## 八、Performance Budget

### 8.1 Lighthouse 目标

| 指标 | 目标 | 说明 |
|---|---|---|
| Performance | ≥ 90 | 首屏性能 |
| Accessibility | ≥ 90 | 可访问性 |
| Best Practices | ≥ 90 | 最佳实践 |
| SEO | ≥ 90 | 搜索引擎优化 |

### 8.2 资源预算

| 资源 | 预算 | 说明 |
|---|---|---|
| JS Bundle | < 300KB | gzip 后 |
| CSS | < 50KB | gzip 后 |
| Images | < 500KB | 所有图片总和 |
| First Paint | < 1.5s | 首屏渲染 |
| CLS | < 0.1 | 布局偏移 |
| LCP | < 2.5s | 最大内容绘制 |
| FID | < 100ms | 首次输入延迟 |

### 8.3 优化策略

```tsx
// ❌ 禁止：动态 import 滥用
const HeavyComponent = dynamic(() => import("./HeavyComponent")); // 滥用

// ✅ 必须：按需加载
const ReplayPrediction = dynamic(() => import("./ReplayPrediction"), {
  loading: () => <Skeleton />,
  ssr: false,  // 播放器不需要 SSR
});
```

---

## 九、Error Boundary 规范

### 9.1 全局 Error Boundary

```tsx
// components/ErrorBoundary.tsx
"use client";

import { Component, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="flex flex-col items-center justify-center min-h-[400px] gap-4 p-8">
            <AlertTriangle className="w-12 h-12 text-yellow" />
            <h2 className="text-xl font-semibold text-text">Prediction snapshot is unavailable</h2>
            <p className="text-muted">Something went wrong loading the tournament data.</p>
            <div className="flex gap-3">
              <Button onClick={() => window.location.reload()}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button variant="outline" onClick={() => this.setState({ hasError: false, error: null })}>
                Try Again
              </Button>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
```

### 9.2 Snapshot Error State

```tsx
// lib/tournament/loader/snapshot.loader.ts
export class SnapshotLoadError extends Error {
  constructor(
    message: string,
    public code: "NOT_FOUND" | "PARSE_ERROR" | "NETWORK_ERROR" | "VALIDATION_ERROR"
  ) {
    super(message);
    this.name = "SnapshotLoadError";
  }
}

// 使用示例
try {
  const snapshot = await loadSnapshot();
} catch (error) {
  if (error instanceof SnapshotLoadError) {
    // 处理特定错误
    switch (error.code) {
      case "NOT_FOUND":
        return <SnapshotNotFound />;
      case "VALIDATION_ERROR":
        return <SnapshotCorrupted />;
    }
  }
}
```

---

## 十、Testing 规范

### 10.1 Snapshot Contract Test（增强版）

> **P0 - 必须检查数据类型、范围、格式**

```typescript
// __tests__/snapshot-contract.test.ts
describe("Snapshot Contract - 增强版", () => {

  describe("ISO8601 时间格式验证", () => {
    it("snapshot_time 必须是有效的 ISO8601", async () => {
      const snapshot = await loadSnapshot();
      const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;
      expect(snapshot.snapshot_time).toMatch(isoRegex);
    });

    it("expires_at 必须是有效的 ISO8601", async () => {
      const snapshot = await loadSnapshot();
      const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;
      expect(snapshot.expires_at).toMatch(isoRegex);
    });
  });

  describe("Confidence Level 枚举验证", () => {
    it("confidence 必须是 High/Medium/Low", async () => {
      const snapshot = await loadSnapshot();

      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        expect(["High", "Medium", "Low"]).toContain(match.confidence);
      }
    });

    it("confidence 不能是 undefined/null/空字符串", async () => {
      const snapshot = await loadSnapshot();

      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        expect(match.confidence).toBeDefined();
        expect(typeof match.confidence).toBe("string");
        expect(match.confidence.length).toBeGreaterThan(0);
      }
    });
  });

  describe("Probability 范围验证", () => {
    it("champion_probability 必须在 0~1 之间", async () => {
      const snapshot = await loadSnapshot();
      expect(snapshot.champion_probability).toBeGreaterThanOrEqual(0);
      expect(snapshot.champion_probability).toBeLessThanOrEqual(1);
    });

    it("所有概率字段必须是百分比字符串", async () => {
      const snapshot = await loadSnapshot();
      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        expect(match.home_win_prob).toMatch(/^\d+(\.\d+)?%$/);
        expect(match.draw_prob).toMatch(/^\d+(\.\d+)?%$/);
        expect(match.away_win_prob).toMatch(/^\d+(\.\d+)?%$/);
      }
    });
  });

  describe("Reasoning 验证", () => {
    it("每场比赛必须有非空 reasoning", async () => {
      const snapshot = await loadSnapshot();
      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        expect(match.reasoning).toBeDefined();
        expect(typeof match.reasoning).toBe("string");
        expect(match.reasoning.length).toBeGreaterThan(10); // 至少 10 个字符
      }
    });

    it("reasoning 不能只是 'N/A' 或占位符", async () => {
      const snapshot = await loadSnapshot();
      const allMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches);

      for (const match of allMatches) {
        const invalidReasonings = ["N/A", "TBD", "pending", "-", ""];
        expect(invalidReasonings).not.toContain(match.reasoning.toLowerCase());
      }
    });
  });

  describe("比赛数量验证", () => {
    it("必须有 72 场小组赛", async () => {
      const snapshot = await loadSnapshot();
      const totalMatches = Object.values(snapshot.group_predictions)
        .flatMap((g) => g.matches).length;
      expect(totalMatches).toBe(72);
    });
  });

  describe("Monte Carlo 验证", () => {
    it("monte_carlo_simulations 必须 >= 10000", async () => {
      const snapshot = await loadSnapshot();
      expect(snapshot.monte_carlo_simulations).toBeGreaterThanOrEqual(10000);
    });

    it("reasoning_chain 必须包含 monte_carlo_tool", async () => {
      const snapshot = await loadSnapshot();
      const hasMonteCarlo = snapshot.reasoning_chain.some(
        (entry) => entry.tool === "monte_carlo_tool"
      );
      expect(hasMonteCarlo).toBe(true);
    });
  });

  describe("Champion 数据验证", () => {
    it("champion 不能为空", async () => {
      const snapshot = await loadSnapshot();
      expect(snapshot.champion).toBeDefined();
      expect(snapshot.champion.length).toBeGreaterThan(0);
    });

    it("champion_probability 必须是数字", async () => {
      const snapshot = await loadSnapshot();
      expect(typeof snapshot.champion_probability).toBe("number");
    });
  });
});
```

---

## 十一、Git 规范

### 11.1 Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

示例：
```
feat(tournament): add ChampionPathViewModel

Add ChampionPathViewModel for Champion Journey display.
Implements UI Adapter pattern for match card data.

Closes #12
```

### 11.2 Branch 命名

```
feature/TP-1-foundation
feature/TP-2-narrative
feature/TP-3-bracket
bugfix/snapshot-error
hotfix/production-crash
```

### 11.3 PR 规范

```
## Summary
- 简要说明改动

## Test Plan
- [ ] 运行 Snapshot Contract Test
- [ ] 测试 Replay Prediction
- [ ] 测试 Mobile Responsive

## Checklist
- [ ] 代码遵循 Engineering Guidelines
- [ ] 无 console.error
- [ ] Lighthouse Performance ≥ 90
```

---

## 十二、文档体系锁定

```
本文档体系已完整，锁定如下：

✅ FRONTEND_ARCHITECTURE.md     — 前端架构设计
✅ PRODUCT_SPEC.md               — 产品规格
✅ TOURNAMENT_ENGINE_DESIGN.md  — Tournament Presentation 设计
✅ ENGINEERING_GUIDELINES.md    — 工程规范（本文档）

后续：
  - 新增文档：PR + Code Review
  - 修改文档：仅允许 typo 修复
  - 全部进入 Engineering Phase
```

---

## 十三、版本历史

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-07-05 | 初始版本，锁定文档体系 |
| v2.0 | 2026-07-05 | 升级核心规则：Presentation Never Thinks、Adapter 纯映射、ViewModel 单一职责、Snapshot 隐藏、类型文件精简、增强 Snapshot Contract Test |

---

## 附录：CTO Code Review Checklist

### P0（必须通过）

- [ ] Loader 职责单一，只读取不转换
- [ ] Adapter 只做映射，无 if/else > 2 层
- [ ] ViewModel UI 化，不暴露原始数据字段
- [ ] **Presentation Never Thinks** — 前端不重新计算
- [ ] Snapshot 类型只在 Loader 层可见
- [ ] 增强 Snapshot Contract Test 通过

### P1（建议通过）

- [ ] 类型文件只有 2 个：Domain + UI
- [ ] VM 不直接调 Adapter
- [ ] Component 无状态，只消费 ViewModel
- [ ] Error Boundary 按页面拆分
- [ ] Accessibility 支持 Tab/Enter

### P2（后期优化）

- [ ] Design Token 完善（Spacing、Radius、Shadow、Typography）
- [ ] Animation 统一状态机
- [ ] Performance Budget 达标
