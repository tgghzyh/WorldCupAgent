/**
 * Snapshot Adapter
 * Converts latest.json to intermediate format
 * Future: can be extended to support FastAPI responses
 * 
 * Rule: Adapter 只做纯映射，不做业务计算
 */

import type { Snapshot } from "@/lib/tournament/types";

export interface SnapshotAdapterOutput {
  champion: string;
  championProbability: number;
  runnerUp: string;
  thirdPlace: string;
  groups: GroupAdapter[];
  knockout: KnockoutAdapter;
  reasoningChain: ReasoningChainAdapter[];
  monteCarloStats: MonteCarloStatsAdapter;
  metadata: MetadataAdapter;
}

export interface GroupAdapter {
  letter: string;
  name: string;
  matches: MatchAdapter[];
  standings: StandingAdapter[];
  qualifiers: string[];
}

export interface MatchAdapter {
  id: string;
  homeTeam: string;
  awayTeam: string;
  homeWinProb: number;
  drawProb: number;
  awayWinProb: number;
  predictedScore: string;
  hasRealScore: boolean;
  reasoning: string;
  confidence: number;
  confidenceLevel: "High" | "Medium" | "Low";
  scheduledDate: string;
  stage: string;
  roundNumber: number;
}

export interface StandingAdapter {
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

export interface KnockoutAdapter {
  predictedChampion: string;
  championProbability: number;
  rounds: {
    roundOf16: KnockoutMatchAdapter[];
    quarterFinals: KnockoutMatchAdapter[];
    semiFinals: KnockoutMatchAdapter[];
    thirdPlace: KnockoutMatchAdapter;
    final: KnockoutMatchAdapter;
  };
  championProbabilities: Record<string, number>;
}

export interface KnockoutMatchAdapter {
  id: string;
  homeTeam: string;
  awayTeam: string;
  homeWinProb: number;
  drawProb: number;
  awayWinProb: number;
  predictedScore: string;
  hasRealScore: boolean;
  winner: string;
  loser: string;
  reasoning: string;
  confidence: number;
  confidenceLevel: "High" | "Medium" | "Low";
}

export interface ReasoningChainAdapter {
  tool: string;
  action: string;
  result: string;
  durationMs: number;
  timestamp: string;
  iterations?: number;
}

export interface MonteCarloStatsAdapter {
  iterations: number;
  championDistribution: Record<string, number>;
  durationMs: number;
  durationSec: number;
  durationMin: number;
}

export interface MetadataAdapter {
  knowledgeVersion: string;
  predictionVersion: string;
  snapshotTime: string;
  expiresAt: string;
  createdBy: string;
  generationDurationMs: number;
  monteCarloSimulations: number;
}

/**
 * Parse percentage string to decimal
 */
function parseProb(prob: string): number {
  return parseFloat(prob.replace("%", "")) / 100;
}

function getConfidenceLevel(confidence: string): "High" | "Medium" | "Low" {
  const normalized = confidence.trim().toLowerCase();
  if (normalized === "high" || normalized === "medium" || normalized === "low") {
    return (normalized.charAt(0).toUpperCase() + normalized.slice(1)) as
      | "High"
      | "Medium"
      | "Low";
  }

  const value = Number.parseFloat(normalized.replace("%", ""));
  if (Number.isNaN(value)) {
    return "Medium";
  }
  if (value >= 70) {
    return "High";
  }
  if (value >= 45) {
    return "Medium";
  }
  return "Low";
}

/**
 * Snapshot Adapter - converts latest.json to intermediate format
 */
export class SnapshotAdapter {
  /**
   * Convert latest.json to intermediate format
   */
  static fromJson(snapshot: Snapshot): SnapshotAdapterOutput {
    return {
      champion: snapshot.champion,
      championProbability: snapshot.champion_probability,
      runnerUp: snapshot.runner_up,
      thirdPlace: snapshot.third_place,
      groups: this.convertGroups(snapshot),
      knockout: this.convertKnockout(snapshot),
      reasoningChain: this.convertReasoningChain(snapshot),
      monteCarloStats: this.convertMonteCarloStats(snapshot),
      metadata: this.convertMetadata(snapshot),
    };
  }

  private static convertGroups(snapshot: Snapshot): GroupAdapter[] {
    return Object.entries(snapshot.group_predictions).map(
      ([letter, group]) => ({
        letter,
        name: `Group ${letter}`,
        matches: group.matches.map((m) => ({
          id: m.id,
          homeTeam: m.home_team,
          awayTeam: m.away_team,
          homeWinProb: parseProb(m.home_win_prob),
          drawProb: parseProb(m.draw_prob),
          awayWinProb: parseProb(m.away_win_prob),
          predictedScore: m.predicted_score,
          hasRealScore: false,
          reasoning: m.reasoning,
          confidence: parseProb(m.confidence),
          confidenceLevel: getConfidenceLevel(m.confidence),
          scheduledDate: m.scheduled_date,
          stage: m.stage,
          roundNumber: m.round_number,
        })),
        standings: group.standings.map((s) => ({
          team: s.team,
          played: s.played,
          won: s.won,
          drawn: s.drawn,
          lost: s.lost,
          goalsFor: s.goals_for,
          goalsAgainst: s.goals_against,
          goalDiff: s.goal_diff,
          points: s.points,
        })),
        qualifiers: group.qualifiers,
      })
    );
  }

  private static convertKnockout(
    snapshot: Snapshot
  ): KnockoutAdapter {
    const { rounds } = snapshot.knockout_predictions;

    return {
      predictedChampion: snapshot.knockout_predictions.predicted_champion,
      championProbability:
        parseProb(snapshot.knockout_predictions.champion_probability),
      rounds: {
        roundOf16: rounds.round_of_16.map(this.convertKnockoutMatch),
        quarterFinals: rounds.quarter_finals.map(this.convertKnockoutMatch),
        semiFinals: rounds.semi_finals.map(this.convertKnockoutMatch),
        thirdPlace: this.convertKnockoutMatch(rounds.third_place),
        final: this.convertKnockoutMatch(rounds.final),
      },
      championProbabilities: Object.fromEntries(
        Object.entries(snapshot.knockout_predictions.champion_probabilities).map(
          ([team, prob]) => [team, parseProb(prob)]
        )
      ),
    };
  }

  private static convertKnockoutMatch(
    m: Snapshot["knockout_predictions"]["rounds"]["round_of_16"][number]
  ): KnockoutMatchAdapter {
    return {
      id: m.id,
      homeTeam: m.home_team,
      awayTeam: m.away_team,
      homeWinProb: parseProb(m.home_win_prob),
      drawProb: parseProb(m.draw_prob),
      awayWinProb: parseProb(m.away_win_prob),
      predictedScore: m.predicted_score,
      hasRealScore: false,
      winner: m.winner,
      loser: m.loser,
      reasoning: m.reasoning,
      confidence: parseProb(m.confidence),
      confidenceLevel: getConfidenceLevel(m.confidence),
    };
  }

  private static convertReasoningChain(
    snapshot: Snapshot
  ): ReasoningChainAdapter[] {
    return snapshot.reasoning_chain.map((entry) => ({
      tool: entry.tool,
      action: entry.action,
      result: entry.result,
      durationMs: entry.duration_ms,
      timestamp: entry.timestamp,
      iterations: entry.iterations,
    }));
  }

  private static convertMonteCarloStats(
    snapshot: Snapshot
  ): MonteCarloStatsAdapter {
    const monteCarloEntry = snapshot.reasoning_chain.find(
      (entry) => entry.tool === "monte_carlo_tool"
    );
    const durationMs = monteCarloEntry?.duration_ms ?? 0;
    const durationSec = Math.round(durationMs / 1000);
    const durationMin = Math.floor(durationSec / 60);

    return {
      iterations: snapshot.monte_carlo_simulations,
      championDistribution: Object.fromEntries(
        Object.entries(snapshot.knockout_predictions.champion_probabilities).map(
          ([team, prob]) => {
            const match = prob.match(/(\d+)\/(\d+)/);
            if (match) {
              return [team, parseInt(match[1], 10)];
            }
            return [team, 0];
          }
        )
      ),
      durationMs,
      durationSec,
      durationMin,
    };
  }

  private static convertMetadata(snapshot: Snapshot): MetadataAdapter {
    return {
      knowledgeVersion: snapshot.knowledge_version,
      predictionVersion: snapshot.prediction_version,
      snapshotTime: snapshot.snapshot_time,
      expiresAt: snapshot.expires_at,
      createdBy: snapshot.created_by,
      generationDurationMs: snapshot.generation_duration_ms,
      monteCarloSimulations: snapshot.monte_carlo_simulations,
    };
  }
}
