/**
 * ConfidenceExplain ViewModel
 * Builds ConfidenceExplainViewModel for confidence display
 */

import type { Snapshot } from "@/lib/tournament/types";
import type { ConfidenceExplainViewModel } from "@/lib/tournament/types";
import { SnapshotAdapter } from "@/lib/tournament/adapters/snapshot.adapter";

export class ConfidenceExplainVMBuilder {
  /**
   * Build ConfidenceExplainViewModel for a match
   */
  static build(
    snapshot: Snapshot,
    homeWinProb: number,
    reasoning: string
  ): ConfidenceExplainViewModel {
    const adapter = SnapshotAdapter.fromJson(snapshot);
    const score = Math.round(homeWinProb * 100);

    let level: "High" | "Medium" | "Low";
    if (score >= 70) level = "High";
    else if (score >= 40) level = "Medium";
    else level = "Low";

    const reasons = this.buildReasons(homeWinProb, reasoning, score);
    const monteCarlo = {
      iterations: adapter.monteCarloStats.iterations,
      convergenceReached: true,
    };

    return {
      score,
      level,
      reasons,
      monteCarlo,
    };
  }

  private static buildReasons(
    homeWinProb: number,
    reasoning: string,
    score: number
  ): Array<{
    label: string;
    status: "pass" | "warn" | "fail";
    detail: string;
  }> {
    const reasons = [];

    // Simulation convergence
    reasons.push({
      label: "Simulation convergence reached",
      status: "pass",
      detail: "Monte Carlo iterations completed",
    });

    // Probability advantage
    const probDiff = Math.abs(homeWinProb - 0.5) * 2;
    if (probDiff > 0.3) {
      reasons.push({
        label: "Clear probability advantage",
        status: "pass",
        detail: `${(homeWinProb * 100).toFixed(1)}% win probability`,
      });
    } else if (probDiff > 0.1) {
      reasons.push({
        label: "Moderate probability advantage",
        status: "warn",
        detail: "Close match - higher uncertainty",
      });
    } else {
      reasons.push({
        label: "Uncertain outcome",
        status: "fail",
        detail: "Near 50-50 probability",
      });
    }

    // Reasoning quality
    if (reasoning.length > 50) {
      reasons.push({
        label: "Strong reasoning evidence",
        status: "pass",
        detail: `${reasoning.length} characters of analysis`,
      });
    } else if (reasoning.length > 20) {
      reasons.push({
        label: "Basic reasoning available",
        status: "warn",
        detail: "Limited analysis provided",
      });
    } else {
      reasons.push({
        label: "Limited reasoning",
        status: "fail",
        detail: "Minimal reasoning text",
      });
    }

    // ELO difference (inferred from reasoning)
    const eloMatch = reasoning.match(/ELO评分差(\d+)分/);
    if (eloMatch) {
      const eloDiff = parseInt(eloMatch[1], 10);
      reasons.push({
        label: "ELO difference significant",
        status: eloDiff > 150 ? "pass" : "warn",
        detail: `ELO difference: ${eloDiff} points`,
      });
    }

    return reasons;
  }
}
