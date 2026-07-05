/**
 * latest.json Type Definitions
 * Maps all fields from data/snapshots/latest.json
 * Single Source of Truth for snapshot data
 */

export interface GroupMatch {
  id: string;
  match_type: "group";
  home_team: string;
  away_team: string;
  scheduled_date: string;
  stage: string;
  round_number: number;
  predicted_score: string;
  home_win_prob: string;
  draw_prob: string;
  away_win_prob: string;
  confidence: string;
  reasoning: string;
}

export interface Standing {
  team: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
}

export interface GroupData {
  group_name: string;
  matches: GroupMatch[];
  standings: Standing[];
  qualifiers: string[];
}

export interface KnockoutMatch {
  id: string;
  match_type: "knockout";
  home_team: string;
  away_team: string;
  stage: string;
  home_win_prob: string;
  draw_prob: string;
  away_win_prob: string;
  predicted_score: string;
  winner: string;
  loser: string;
  reasoning: string;
  confidence: string;
}

export interface KnockoutRounds {
  round_of_16: KnockoutMatch[];
  quarter_finals: KnockoutMatch[];
  semi_finals: KnockoutMatch[];
  third_place: KnockoutMatch;
  final: KnockoutMatch;
}

export interface KnockoutPredictions {
  predicted_champion: string;
  champion_probability: string;
  rounds: KnockoutRounds;
  champion_probabilities: Record<string, string>;
}

export interface ReasoningChainEntry {
  tool: string;
  action: string;
  result: string;
  duration_ms: number;
  timestamp: string;
  iterations?: number;
}

export interface Snapshot {
  knowledge_version: string;
  prediction_version: string;
  snapshot_time: string;
  expires_at: string;
  teams_snapshot: Record<string, unknown>;
  fifa_rankings_snapshot: Record<string, unknown>;
  elo_ratings_snapshot: Record<string, unknown>;
  champion: string;
  runner_up: string;
  third_place: string;
  champion_probability: number;
  group_predictions: Record<string, GroupData>;
  knockout_predictions: KnockoutPredictions;
  reasoning_chain: ReasoningChainEntry[];
  llm_analysis: string;
  created_by: string;
  generation_duration_ms: number;
  monte_carlo_simulations: number;
}

export type GroupLetter = "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L";

export type ConfidenceLevel = "High" | "Medium" | "Low";

export type KnockoutStage =
  | "round_of_16"
  | "quarter_finals"
  | "semi_finals"
  | "third_place"
  | "final";

export type MatchId = string;

export type TeamName = string;

export type Probability = number;
