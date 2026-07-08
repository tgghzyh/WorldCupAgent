/**
 * Bracket ViewModel
 * Builds BracketViewModel for Bracket display
 */

import type { Snapshot } from "@/lib/tournament/types";
import type { BracketViewModel, BracketNodeViewModel } from "@/lib/tournament/types";
import { SnapshotAdapter } from "@/lib/tournament/adapters/snapshot.adapter";

export class BracketVMBuilder {
  /**
   * Build complete BracketViewModel
   */
  static build(snapshot: Snapshot): BracketViewModel {
    const adapter = SnapshotAdapter.fromJson(snapshot);

    const roundOf16 = this.buildRoundOf16(adapter);
    const quarterFinals = this.buildQuarterFinals(adapter);
    const semiFinals = this.buildSemiFinals(adapter);
    const thirdPlace = this.buildThirdPlace(adapter);
    const final = this.buildFinal(adapter);
    const championPath = this.buildChampionPath(adapter);

    return {
      roundOf16,
      quarterFinals,
      semiFinals,
      thirdPlace,
      final,
      championPath,
    };
  }

  private static buildRoundOf16(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>
  ): BracketNodeViewModel[] {
    return adapter.knockout.rounds.roundOf16.map((m, index) => ({
      nodeId: `r16_${index}`,
      matchId: m.id,
      homeTeam: m.homeTeam,
      awayTeam: m.awayTeam,
      homeWinProb: m.homeWinProb,
      awayWinProb: m.awayWinProb,
      winner: m.winner,
      predictedScore: m.predictedScore,
      reasoning: {
        text: m.reasoning,
        source: "monte_carlo_tool",
        isVerified: true,
      },
      isExpanded: false,
      stage: "round_of_16",
      stageLabel: "1/8决赛",
      stageOrder: 1,
    }));
  }

  private static buildQuarterFinals(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>
  ): BracketNodeViewModel[] {
    return adapter.knockout.rounds.quarterFinals.map((m, index) => ({
      nodeId: `qf_${index}`,
      matchId: m.id,
      homeTeam: m.homeTeam,
      awayTeam: m.awayTeam,
      homeWinProb: m.homeWinProb,
      awayWinProb: m.awayWinProb,
      winner: m.winner,
      predictedScore: m.predictedScore,
      reasoning: {
        text: m.reasoning,
        source: "monte_carlo_tool",
        isVerified: true,
      },
      isExpanded: false,
      stage: "quarter_finals",
      stageLabel: "1/4决赛",
      stageOrder: 2,
    }));
  }

  private static buildSemiFinals(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>
  ): BracketNodeViewModel[] {
    return adapter.knockout.rounds.semiFinals.map((m, index) => ({
      nodeId: `sf_${index}`,
      matchId: m.id,
      homeTeam: m.homeTeam,
      awayTeam: m.awayTeam,
      homeWinProb: m.homeWinProb,
      awayWinProb: m.awayWinProb,
      winner: m.winner,
      predictedScore: m.predictedScore,
      reasoning: {
        text: m.reasoning,
        source: "monte_carlo_tool",
        isVerified: true,
      },
      isExpanded: false,
      stage: "semi_finals",
      stageLabel: "半决赛",
      stageOrder: 3,
    }));
  }

  private static buildThirdPlace(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>
  ): BracketNodeViewModel {
    const m = adapter.knockout.rounds.thirdPlace;
    return {
      nodeId: "third_place",
      matchId: m.id,
      homeTeam: m.homeTeam,
      awayTeam: m.awayTeam,
      homeWinProb: m.homeWinProb,
      awayWinProb: m.awayWinProb,
      winner: m.winner,
      predictedScore: m.predictedScore,
      reasoning: {
        text: m.reasoning,
        source: "monte_carlo_tool",
        isVerified: true,
      },
      isExpanded: false,
      stage: "third_place",
      stageLabel: "三四名决赛",
      stageOrder: 4,
    };
  }

  private static buildFinal(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>
  ): BracketNodeViewModel {
    const m = adapter.knockout.rounds.final;
    return {
      nodeId: "final",
      matchId: m.id,
      homeTeam: m.homeTeam,
      awayTeam: m.awayTeam,
      homeWinProb: m.homeWinProb,
      awayWinProb: m.awayWinProb,
      winner: m.winner,
      predictedScore: m.predictedScore,
      reasoning: {
        text: m.reasoning,
        source: "monte_carlo_tool",
        isVerified: true,
      },
      isExpanded: false,
      stage: "final",
      stageLabel: "决赛",
      stageOrder: 5,
    };
  }

  private static buildChampionPath(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>
  ) {
    const champion = adapter.champion;
    const stages = [
      { matches: adapter.knockout.rounds.roundOf16, key: "round_of_16", label: "1/8决赛" },
      { matches: adapter.knockout.rounds.quarterFinals, key: "quarter_finals", label: "1/4决赛" },
      { matches: adapter.knockout.rounds.semiFinals, key: "semi_finals", label: "半决赛" },
      { matches: [adapter.knockout.rounds.final], key: "final", label: "决赛" },
    ] as const;

    const path: Array<{
      stage: string;
      stageLabel: string;
      vs: string;
      winProb: number;
      matchId: string;
      reasoning: { text: string; source: string; isVerified: boolean };
    }> = [];

    for (const stage of stages) {
      const match = stage.matches.find(
        (m) => m.homeTeam === champion || m.awayTeam === champion
      );

      if (match) {
        const isHome = match.homeTeam === champion;
        path.push({
          stage: stage.key,
          stageLabel: stage.label,
          vs: isHome ? match.awayTeam : match.homeTeam,
          winProb: isHome ? match.homeWinProb : match.awayWinProb,
          matchId: match.id,
          reasoning: {
            text: match.reasoning,
            source: "monte_carlo_tool",
            isVerified: true,
          },
        });
      }
    }

    return path;
  }
}
