import {
  Activity,
  BarChart3,
  Brain,
  CalendarClock,
  GitCompare,
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
  { label: "Compare", href: "/compare", icon: GitCompare },
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

export const compareChanges = [
  { subject: "Argentina champion probability", before: "39%", after: "42%", delta: "+3.0pp", direction: "up" },
  { subject: "Spain finalist probability", before: "31%", after: "34%", delta: "+3.0pp", direction: "up" },
  { subject: "Brazil semi-final probability", before: "48%", after: "45%", delta: "-3.0pp", direction: "down" },
  { subject: "Mexico upset chance vs Argentina", before: "17%", after: "20%", delta: "+3.0pp", direction: "up" },
];

export const demoSteps = [
  { title: "Champion answer", text: "Open with the projected champion and the probability range.", icon: Trophy },
  { title: "Match reasoning", text: "Show one match and explain the model factors in plain language.", icon: LineChart },
  { title: "Tournament path", text: "Walk through the bracket route and identify unstable rounds.", icon: Medal },
  { title: "Trust layer", text: "Close with freshness, simulations, and explainability signals.", icon: ShieldCheck },
];

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
