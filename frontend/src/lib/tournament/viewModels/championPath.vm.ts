/**
 * ChampionPath ViewModel
 * Builds ChampionPathViewModel for Champion Journey display.
 */

import type {
  ChampionLegViewModel,
  ChampionPathViewModel,
  JourneyStepViewModel,
  Snapshot,
} from "@/lib/tournament/types";
import { SnapshotAdapter } from "@/lib/tournament/adapters/snapshot.adapter";

export class ChampionPathVMBuilder {
  static build(snapshot: Snapshot): ChampionPathViewModel {
    const adapter = SnapshotAdapter.fromJson(snapshot);
    const champion = adapter.knockout.predictedChampion;
    const probability = adapter.knockout.championProbability;

    const legs = this.buildChampionLegs(adapter, champion);
    const narrative = this.buildNarrative(champion, legs);
    const journeySteps = this.buildJourneySteps(adapter, legs);

    return {
      champion,
      probability,
      monteCarlo: {
        iterations: adapter.monteCarloStats.iterations,
        wins:
          adapter.monteCarloStats.championDistribution[champion] ||
          adapter.monteCarloStats.iterations,
        total: adapter.monteCarloStats.iterations,
        durationSec: adapter.monteCarloStats.durationSec,
      },
      legs,
      narrative,
      journeySteps,
    };
  }

  private static buildChampionLegs(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>,
    champion: string
  ): ChampionLegViewModel[] {
    const { rounds } = adapter.knockout;
    const stages = [
      { key: "roundOf16", label: "Round of 16" },
      { key: "quarterFinals", label: "Quarter-finals" },
      { key: "semiFinals", label: "Semi-finals" },
      { key: "final", label: "Final" },
    ] as const;

    return stages.flatMap((stage) => {
      const round = rounds[stage.key];
      const matches = Array.isArray(round) ? round : [round];
      const match = matches.find(
        (candidate) =>
          candidate.homeTeam === champion || candidate.awayTeam === champion
      );

      if (!match) {
        return [];
      }

      const isHome = match.homeTeam === champion;
      return [
        {
          stage: stage.key,
          stageLabel: stage.label,
          vs: isHome ? match.awayTeam : match.homeTeam,
          winProb: isHome ? match.homeWinProb : match.awayWinProb,
          reasoning: {
            text: match.reasoning,
            source: "monte_carlo_tool",
            isVerified: true,
          },
          matchId: match.id,
        },
      ];
    });
  }

  private static buildNarrative(
    champion: string,
    legs: ChampionLegViewModel[]
  ): string {
    const path = legs
      .map(
        (leg) =>
          `${leg.stageLabel} vs ${leg.vs} (${(leg.winProb * 100).toFixed(1)}%)`
      )
      .join(" -> ");

    return `${champion} projected path: ${path}`;
  }

  private static buildJourneySteps(
    adapter: ReturnType<typeof SnapshotAdapter.fromJson>,
    legs: ChampionLegViewModel[]
  ): JourneyStepViewModel[] {
    const steps: JourneyStepViewModel[] = [];
    const championGroup = adapter.groups.find((group) =>
      group.qualifiers.includes(adapter.champion)
    );

    if (championGroup) {
      steps.push({
        stage: "group_stage",
        stageLabel: "Group Stage",
        color: "green",
        headline: `AI predicted ${adapter.champion} to top Group ${championGroup.letter}`,
        detail: `Champion probability ${(adapter.championProbability * 100).toFixed(0)}%`,
        reasoning: {
          text: "Based on group stage predictions",
          source: "group_prediction_tool",
          isVerified: true,
        },
      });
    }

    const stageColors: Record<string, "green" | "yellow" | "blue"> = {
      roundOf16: "green",
      quarterFinals: "yellow",
      semiFinals: "yellow",
      final: "blue",
    };

    for (const leg of legs) {
      const isFinal = leg.stage === "final";
      steps.push({
        stage: leg.stage,
        stageLabel: leg.stageLabel,
        color: isFinal ? "blue" : stageColors[leg.stage] || "green",
        headline: isFinal
          ? `Champion probability reached ${(leg.winProb * 100).toFixed(1)}%`
          : `${adapter.champion} advanced with ${(leg.winProb * 100).toFixed(1)}% probability`,
        detail: `vs ${leg.vs}`,
        winProb: leg.winProb,
        reasoning: leg.reasoning,
      });
    }

    steps.push({
      stage: "champion",
      stageLabel: "Champion",
      color: "gold",
      headline: adapter.champion,
      detail: `Monte Carlo: ${adapter.monteCarloStats.iterations.toLocaleString()} iterations`,
      reasoning: {
        text: "Champion confirmed via Monte Carlo simulation",
        source: "monte_carlo_tool",
        isVerified: true,
      },
    });

    return steps;
  }
}
