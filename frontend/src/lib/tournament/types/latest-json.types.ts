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
  winner?: string;
  llm_provider?: string;
  llm_model?: string;
  llm_prompt_version?: string;
  llm_reasoning_factors?: LLMReasoningFactor[];
  probability_model?: MatchProbabilityModel;
  llm_reflection?: PredictionReflection;
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
  llm_provider?: string;
  llm_model?: string;
  llm_prompt_version?: string;
  llm_reasoning_factors?: LLMReasoningFactor[];
  probability_model?: MatchProbabilityModel;
  llm_reflection?: PredictionReflection;
}

export interface LLMReasoningFactor {
  id?: string;
  type: "fitness" | "tactical" | "injury" | "home" | "form" | "transition";
  label: string;
  description: string;
  weight: number;
}

export interface TeamIntelligence {
  team: string;
  group?: string;
  ranking?: {
    fifa_rank?: number | null;
    elo?: number | null;
  };
  overall_strength: number;
  components: Record<"attack" | "defense" | "midfield" | "squad_depth" | "coach_tactics" | "tournament_experience" | "form", number>;
  tactical_profile: string;
  strengths: string[];
  risks: string[];
  key_players: string[];
  summary: string;
  evidence: string[];
  data_confidence: "High" | "Medium" | "Low";
  source: string;
  llm_provider?: string;
  llm_model?: string;
  llm_prompt_version?: string;
}

export interface MatchProbabilityModel {
  model_version: string;
  method: string;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  home_rating?: number;
  away_rating?: number;
  home_advantage?: number;
}

export interface PredictionReflection {
  verdict: "pass" | "caution" | "inconsistent";
  logic_score: number;
  summary: string;
  checks: Array<{
    dimension: "probability" | "score" | "evidence" | "bracket";
    verdict: "pass" | "caution" | "inconsistent";
    note: string;
  }>;
  llm_provider?: string;
  llm_model?: string;
  llm_prompt_version?: string;
}

export interface MonteCarloSimulation {
  model_version: string;
  iterations: number;
  seed: number;
  modal_champion?: string;
  modal_champion_probability?: number;
  champion_counts: Record<string, number>;
  champion_probabilities: Record<string, number>;
  runner_up_probabilities: Record<string, number>;
  third_place_probabilities: Record<string, number>;
  group_qualification_probabilities: Record<string, number>;
  advancement_probabilities: Record<string, Record<string, number>>;
}

export interface KnockoutRounds {
  round_of_32?: KnockoutMatch[];
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
  champion_probabilities: Record<string, string>;
  team_intelligence?: Record<string, TeamIntelligence>;
  simulation?: MonteCarloSimulation;
  reasoning_chain: ReasoningChainEntry[];
  llm_analysis: string;
  created_by: string;
  generation_duration_ms: number;
  monte_carlo_simulations: number;
}

export type GroupLetter = "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L";

export type ConfidenceLevel = "High" | "Medium" | "Low";

export type KnockoutStage =
  | "round_of_32"
  | "round_of_16"
  | "quarter_finals"
  | "semi_finals"
  | "third_place"
  | "final";

export type MatchId = string;

export type TeamName = string;

export type Probability = number;
