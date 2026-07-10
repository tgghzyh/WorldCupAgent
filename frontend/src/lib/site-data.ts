import {
  Activity,
  BarChart3,
  Brain,
  CalendarClock,
  Home,
  LineChart,
  Medal,
  ShieldCheck,
  Sparkles,
  Trophy,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

export type FeaturedMatch = {
  home: string;
  away: string;
  homeWin: number;
  draw: number;
  awayWin: number;
  score: string;
  confidence: string;
  summary: string;
  factors: Array<{ label: string; value: string; tone: "green" | "gold" | "red" | "neutral" }>;
};

export const navItems: NavItem[] = [
  { label: "Home", href: "/", icon: Home },
  { label: "Match", href: "/match", icon: Activity },
  { label: "Tournament", href: "/tournament", icon: Trophy },
  { label: "Demo", href: "/demo", icon: Sparkles },
];

export const predictionSummary = {
  champion: "Argentina",
  championProbability: 0.42,
  runnerUp: "Spain",
  thirdPlace: "France",
  snapshotTime: "2026-07-07 09:00",
  headline:
    "Argentina remains the projected champion, with Spain and France close enough to keep the bracket genuinely unstable.",
};

export const featuredMatch: FeaturedMatch = {
  home: "Argentina",
  away: "Mexico",
  homeWin: 0.58,
  draw: 0.22,
  awayWin: 0.2,
  score: "2-1",
  confidence: "Medium High",
  summary:
    "Argentina has the stronger baseline profile, but Mexico keeps the match within upset range through defensive compactness and transition speed.",
  factors: [
    { label: "ELO edge", value: "+85", tone: "green" },
    { label: "Recent form", value: "Stable", tone: "gold" },
    { label: "Upset risk", value: "20%", tone: "red" },
  ],
};

export const tournamentPath = [
  { stage: "Round of 16", opponent: "Japan", probability: 0.64, note: "Controlled midfield tempo" },
  { stage: "Quarter-final", opponent: "Portugal", probability: 0.56, note: "Narrow technical edge" },
  { stage: "Semi-final", opponent: "France", probability: 0.52, note: "Highest uncertainty match" },
  { stage: "Final", opponent: "Spain", probability: 0.51, note: "Experience decides margins" },
];

export const bracketRounds = [
  {
    title: "Round of 16",
    matches: ["Argentina vs Japan", "Portugal vs Croatia", "Spain vs USA", "France vs Morocco"],
  },
  {
    title: "Quarter-finals",
    matches: ["Argentina vs Portugal", "Spain vs Netherlands"],
  },
  {
    title: "Semi-finals",
    matches: ["Argentina vs France", "Spain vs Brazil"],
  },
  {
    title: "Final",
    matches: ["Argentina vs Spain"],
  },
];

export const trustSignals = [
  { label: "Prediction model", value: "ELO + simulation", icon: Brain },
  { label: "Simulation runs", value: "10,000", icon: BarChart3 },
  { label: "Refresh cadence", value: "Daily", icon: CalendarClock },
  { label: "Explainability", value: "Factor-based", icon: ShieldCheck },
];

export const demoSteps = [
  {
    title: "Champion answer",
    titleZh: "冠军结论",
    text: "Open with the projected champion and the probability range.",
    textZh: "从预测冠军及其夺冠概率区间开始展示。",
    icon: Trophy,
  },
  {
    title: "Match reasoning",
    titleZh: "单场推理",
    text: "Show one match and explain the model factors in plain language.",
    textZh: "选取一场比赛，用清晰语言说明模型判断因素。",
    icon: LineChart,
  },
  {
    title: "Tournament path",
    titleZh: "晋级路径",
    text: "Walk through the bracket route and identify unstable rounds.",
    textZh: "沿赛程树查看晋级路线，并定位不确定性较高的轮次。",
    icon: Medal,
  },
  {
    title: "Trust layer",
    titleZh: "可信依据",
    text: "Close with freshness, simulations, and explainability signals.",
    textZh: "最后展示数据新鲜度、模拟结果与可解释性依据。",
    icon: ShieldCheck,
  },
];

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
