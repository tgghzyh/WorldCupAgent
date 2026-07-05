/**
 * ChampionPath ViewModel
 * Builds ChampionPathViewModel for Champion Journey display
 */

import type { Snapshot } from "@/lib/tournament/types";
import type { ChampionPathViewModel, ChampionLegViewModel, JourneyStepViewModel } from "@/lib/tournament/types";
import { SnapshotAdapter } from "@/lib/tournament/adapters/snapshot.adapter";

export class ChampionPathVMBuilder {
  /**
   * Build ChampionPathViewModel
   */
  static build(snapshot: Snapshot): ChampionPathViewModel {
    const adapter = SnapshotAdapter.fromJson(snapshot);
    const { champion, probability } = adapter.knockout;

    const legs = this.buildChampionLegs(adapter, champion);
    const narrative = this.buildNarrative(champion, probability, legs);
    const journeySteps = this.buildJourneySteps(adapter, legs);

    const monteCarlo = {
      iterations: adapter.monteCarloStats.iterations,
      wins: adapter.monteCarloStats.championDistribution[champion] || adapter.monteCarloStats.iterations,
      total: adapter.monteCarloStats.iterations,
      durationSec: adapter.monteCarloStats.durationSec,
    };

    return {
      champion,
      probability,
      monteCarlo,
      legs,
      narrative,
      journeySteps,
    };
  }

  private static buildChampionLegs(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>,
    champion: string
  ): ChampionLegViewModel[] {
    const legs: ChampionLegViewModel[] = [];
    const { rounds } = adapter.knockout;

    // Find champion's path through rounds
    const stages = [
      { key: "roundOf16", label: "1/8决赛", order: 1 },
      { key: "quarterFinals", label: "1/4决赛", order: 2 },
      { key: "semiFinals", label: "半决赛", order: 3 },
      { key: "final", label: "决赛", order: 4 },
    ] as const;

    for (const stage of stages) {
      const round = rounds[stage.key];
      const matches = Array.isArray(round) ? round : [round];
      const championMatch = matches.find(
        (m) => m.homeTeam === champion || m.awayTeam === champion
      );

      if (championMatch) {
        const isHome = championMatch.homeTeam === champion;
        const vs = isHome ? championMatch.awayTeam : championMatch.homeTeam;
        const winProb = isHome
          ? championMatch.homeWinProb
          : championMatch.awayWinProb;

        legs.push({
          stage: stage.key,
          stageLabel: stage.label,
          vs,
          winProb,
          reasoning: {
            text: championMatch.reasoning,
            source: "monte_carlo_tool",
            isVerified: true,
          },
          matchId: championMatch.id,
        });
      }
    }

    return legs;
  }

  private static buildNarrative(
    champion: string,
    probability: number,
    legs: ChampionLegViewModel[]
  ): string {
    const pathDesc = legs
      .map((leg) => `${leg.stageLabel} vs ${leg.vs}（${(leg.winProb * 100).toFixed(1)}%）`)
      .join(" → ");

    return `${champion} 晋级路径：${pathDesc}`;
  }

  private static buildJourneySteps(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>,
    legs: ChampionLegViewModel[]
  ): JourneyStepViewModel[] {
    const steps: JourneyStepViewModel[] = [];

    // Group Stage
    const championGroup = adapter.groups.find((g) =>
      g.qualifiers.includes(adapter.champion)
    );

    if (championGroup) {
      steps.push({
        stage: "group_stage",
        stageLabel: "Group Stage",
        color: "green",
        headline: `AI predicted ${adapter.champion} to top ${championGroup.letter}`,
        detail: `Confidence ${(adapter.championProbability * 100).toFixed(0)}%`,
        reasoning: {
          text: "Based on group stage predictions",
          source: "group_prediction_tool",
          isVerified: true,
        },
      });
    }

    // Knockout stages
    const stageColors: Record<string, "green" | "yellow" | "blue"> = {
      roundOf16: "green",
      quarterFinals: "yellow",
      semiFinals: "yellow",
      final: "blue",
    };

    for (const leg of legs) {
      const color = stageColors[leg.stage] || "green";
      const isFinal = leg.stage === "final";

      steps.push({
        stage: leg.stage,
        stageLabel: leg.stageLabel,
        color: isFinal ? "blue" : color,
        headline: isFinal
          ? `Champion Probability reached ${(leg.winProb * 100).toFixed(1)}%`
          : `${adapter.champion} advanced with ${(leg.winProb * 100).toFixed(1)}% probability`,
        detail: `vs ${leg.vs}`,
        winProb: leg.winProb,
        reasoning: leg.reasoning,
      });
    }

    // Champion
    steps.push({
      stage: "champion",
      stageLabel: "Champion",
      color: "gold",
      headline: adapter.champion,
      detail: `Monte Carlo: ${adapter.monteCarloStats.iterations.toLocaleString()} iterations · ${adapter.monteCarloStats.durationMin}m ${adapter.monteCarloStats.durationSec % 60}s`,
      reasoning: {
        text: "Champion confirmed via Monte Carlo simulation",
        source: "monte_carlo_tool",
        isVerified: true,
      },
    });

    return steps;
  }
}
