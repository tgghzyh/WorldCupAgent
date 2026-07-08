/**
 * MatchCard ViewModel
 * Builds MatchCardViewModel from adapter output
 */

import type { Snapshot } from "@/lib/tournament/types";
import type { MatchCardViewModel } from "@/lib/tournament/types";
import { SnapshotAdapter } from "@/lib/tournament/adapters/snapshot.adapter";
import { buildConfidenceExplain } from "@/lib/tournament/types";

export class MatchCardVMBuilder {
  /**
   * Build MatchCardViewModel for a specific match
   */
  static build(snapshot: Snapshot, matchId: string): MatchCardViewModel | null {
    const adapter = SnapshotAdapter.fromJson(snapshot);

    // Find the match in groups or knockout
    let match: {
      id: string;
      homeTeam: string;
      awayTeam: string;
      homeWinProb: number;
      drawProb: number;
      awayWinProb: number;
      predictedScore: string;
      hasRealScore: boolean;
      reasoning: string;
      confidenceLevel: "High" | "Medium" | "Low";
      scheduledDate?: string;
      stage?: string;
    } | null = null;

    // Search in groups
    for (const group of adapter.groups) {
      const found = group.matches.find((m) => m.id === matchId);
      if (found) {
        match = {
          ...found,
          scheduledDate: found.scheduledDate,
          stage: found.stage,
        };
        break;
      }
    }

    // Search in knockout rounds
    if (!match) {
      const knockoutRounds = [
        adapter.knockout.rounds.roundOf16,
        adapter.knockout.rounds.quarterFinals,
        adapter.knockout.rounds.semiFinals,
        adapter.knockout.rounds.thirdPlace,
        adapter.knockout.rounds.final,
      ];

      for (const round of knockoutRounds) {
        const found = Array.isArray(round)
          ? round.find((m) => m.id === matchId)
          : round?.id === matchId
          ? round
          : null;
        if (found) {
          match = found;
          break;
        }
      }
    }

    if (!match) {
      return null;
    }

    const confidence = buildConfidenceExplain(
      match.homeWinProb,
      match.reasoning,
      adapter.monteCarloStats.iterations
    );

    return {
      matchId: match.id,
      title: `${match.homeTeam} vs ${match.awayTeam}`,
      subtitle: match.stage || "Knockout Match",
      kickoff: match.scheduledDate || "TBD",
      prediction: {
        homeWin: match.homeWinProb,
        draw: match.drawProb,
        awayWin: match.awayWinProb,
        predictedWinner: match.homeWinProb > match.awayWinProb ? match.homeTeam : match.awayTeam,
        predictedScore: match.predictedScore,
        hasRealScore: match.hasRealScore,
      },
      confidence: {
        level: match.confidenceLevel,
        score: confidence.score,
        explanation: confidence,
      },
      factors: [], // Factors will be built separately
      reasoning: {
        text: match.reasoning,
        source: "group_prediction_tool",
        isVerified: true,
      },
      snapshot: {
        id: adapter.metadata.predictionVersion,
        generatedAt: adapter.metadata.snapshotTime,
        version: adapter.metadata.knowledgeVersion,
        expiresAt: adapter.metadata.expiresAt,
        status: this.getSnapshotStatus(adapter.metadata.expiresAt),
      },
      status: "Upcoming",
    };
  }

  /**
   * Build all MatchCardViewModels for a group
   */
  static buildGroupMatches(
    snapshot: Snapshot,
    groupLetter: string
  ): MatchCardViewModel[] {
    const adapter = SnapshotAdapter.fromJson(snapshot);
    const group = adapter.groups.find((g) => g.letter === groupLetter);

    if (!group) {
      return [];
    }

    return group.matches.map((match) => {
      const confidence = buildConfidenceExplain(
        match.homeWinProb,
        match.reasoning,
        adapter.monteCarloStats.iterations
      );

      return {
        matchId: match.id,
        title: `${match.homeTeam} vs ${match.awayTeam}`,
        subtitle: match.stage,
        kickoff: match.scheduledDate,
        prediction: {
          homeWin: match.homeWinProb,
          draw: match.drawProb,
          awayWin: match.awayWinProb,
          predictedWinner:
            match.homeWinProb > match.awayWinProb
              ? match.homeTeam
              : match.awayTeam,
          predictedScore: match.predictedScore,
          hasRealScore: match.hasRealScore,
        },
        confidence: {
          level: match.confidenceLevel,
          score: confidence.score,
          explanation: confidence,
        },
        factors: [],
        reasoning: {
          text: match.reasoning,
          source: "group_prediction_tool",
          isVerified: true,
        },
        snapshot: {
          id: adapter.metadata.predictionVersion,
          generatedAt: adapter.metadata.snapshotTime,
          version: adapter.metadata.knowledgeVersion,
          expiresAt: adapter.metadata.expiresAt,
          status: this.getSnapshotStatus(adapter.metadata.expiresAt),
        },
        status: "Upcoming",
      };
    });
  }

  private static getSnapshotStatus(expiresAt: string): "Live" | "Stale" {
    const now = new Date();
    const expires = new Date(expiresAt);
    return now < expires ? "Live" : "Stale";
  }
}
