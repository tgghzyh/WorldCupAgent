/**
 * UI Adapter Types
 * Semantic ViewModels for UI Components
 * Not coupled to JSON structure
 */

import type { ConfidenceLevel } from "./latest-json.types";

// ============================================================
// Base Types
// ============================================================

export interface Prediction {
  homeWin: number;
  draw: number;
  awayWin: number;
  predictedWinner: string;
  predictedScore: string;
  hasRealScore: boolean;
}

export interface WinProbabilityBar {
  homeWin: number;
  draw: number;
  awayWin: number;
  homeTeam: string;
  awayTeam: string;
}

// ============================================================
// Match Card
// ============================================================

export interface MatchCardViewModel {
  matchId: string;
  title: string;
  subtitle: string;
  kickoff: string;
  prediction: Prediction;
  confidence: ConfidenceViewModel;
  factors: FactorCardViewModel[];
  reasoning: ReasoningViewModel;
  snapshot: SnapshotBadgeViewModel;
  status: "Upcoming" | "Live" | "Finished";
}

export interface ConfidenceViewModel {
  level: ConfidenceLevel;
  score: number;
  explanation: ConfidenceExplainViewModel;
}

export interface FactorCardViewModel {
  name: string;
  contribution: number;
  direction: "up" | "down";
  evidence: string;
  confidence: ConfidenceLevel;
}

export interface ReasoningViewModel {
  text: string;
  source: string;
  isVerified: boolean;
}

export interface SnapshotBadgeViewModel {
  id: string;
  generatedAt: string;
  version: string;
  expiresAt: string;
  status: "Live" | "Stale";
}

// ============================================================
// Confidence Explain
// ============================================================

export interface ConfidenceExplainViewModel {
  score: number;
  level: ConfidenceLevel;
  reasons: ConfidenceReason[];
  monteCarlo: MonteCarloInfo;
}

export interface ConfidenceReason {
  label: string;
  status: "pass" | "warn" | "fail";
  detail: string;
}

export interface MonteCarloInfo {
  iterations: number;
  convergenceReached: boolean;
}

// ============================================================
// Bracket
// ============================================================

export interface BracketNodeViewModel {
  nodeId: string;
  matchId: string;
  homeTeam: string;
  awayTeam: string;
  homeWinProb: number;
  awayWinProb: number;
  winner: string;
  predictedScore: string;
  reasoning: ReasoningViewModel;
  isExpanded: boolean;
  stage: string;
  stageLabel: string;
  stageOrder: number;
}

export interface BracketViewModel {
  roundOf16: BracketNodeViewModel[];
  quarterFinals: BracketNodeViewModel[];
  semiFinals: BracketNodeViewModel[];
  thirdPlace: BracketNodeViewModel;
  final: BracketNodeViewModel;
  championPath: ChampionLegViewModel[];
}

// ============================================================
// Champion Path
// ============================================================

export interface ChampionPathViewModel {
  champion: string;
  probability: number;
  monteCarlo: MonteCarloViewModel;
  legs: ChampionLegViewModel[];
  narrative: string;
  journeySteps: JourneyStepViewModel[];
}

export interface ChampionLegViewModel {
  stage: string;
  stageLabel: string;
  vs: string;
  winProb: number;
  reasoning: ReasoningViewModel;
  matchId: string;
}

export interface MonteCarloViewModel {
  iterations: number;
  wins: number;
  total: number;
  durationSec: number;
}

export interface JourneyStepViewModel {
  stage: string;
  stageLabel: string;
  color: "green" | "yellow" | "blue" | "gold";
  headline: string;
  detail: string;
  winProb?: number;
  reasoning: ReasoningViewModel;
}

// ============================================================
// Group Stage
// ============================================================

export interface GroupStageViewModel {
  group: GroupViewModel;
}

export interface GroupViewModel {
  letter: string;
  name: string;
  matches: GroupMatchViewModel[];
  standings: StandingsRowViewModel[];
  qualifiers: string[];
}

export interface GroupMatchViewModel {
  matchId: string;
  homeTeam: string;
  awayTeam: string;
  homeWinProb: number;
  drawProb: number;
  awayWinProb: number;
  reasoning: ReasoningViewModel;
  stage: string;
}

export interface StandingsRowViewModel {
  position: number;
  team: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDiff: number;
  points: number;
}

// ============================================================
// Replay Prediction
// ============================================================

export interface ReplayControlsViewModel {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  playbackRate: 0.5 | 1 | 2;
  progress: number;
  currentTimeDisplay: string;
  durationDisplay: string;
  play: () => void;
  pause: () => void;
  restart: () => void;
  seek: (time: number) => void;
  setPlaybackRate: (rate: 0.5 | 1 | 2) => void;
}

export interface ReplayTimelineViewModel {
  segments: ReplaySegmentViewModel[];
  totalDuration: number;
}

export interface ReplaySegmentViewModel {
  stage: string;
  stageLabel: string;
  startTime: number;
  endTime: number;
  duration: number;
}

// ============================================================
// Error States
// ============================================================

export interface ErrorStateViewModel {
  code: "NOT_FOUND" | "PARSE_ERROR" | "NETWORK_ERROR" | "VALIDATION_ERROR";
  message: string;
  suggestion?: string;
  onRetry?: () => void;
}

export interface LoadingStateViewModel {
  message: string;
  skeleton?: "match" | "bracket" | "champion" | "group";
}
