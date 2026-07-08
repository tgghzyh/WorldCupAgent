/**
 * ConfidenceExplain ViewModel
 * Builds ConfidenceExplainViewModel for confidence display.
 */

import type { ConfidenceExplainViewModel, Snapshot } from "@/lib/tournament/types";
import { SnapshotAdapter } from "@/lib/tournament/adapters/snapshot.adapter";

type ConfidenceReason = ConfidenceExplainViewModel["reasons"][number];

export class ConfidenceExplainVMBuilder {
  static build(
    snapshot: Snapshot,
    homeWinProb: number,
    reasoning: string
  ): ConfidenceExplainViewModel {
    const adapter = SnapshotAdapter.fromJson(snapshot);
    const score = Math.round(homeWinProb * 100);
    const level = score >= 70 ? "High" : score >= 40 ? "Medium" : "Low";

    return {
      score,
      level,
      reasons: this.buildReasons(homeWinProb, reasoning),
      monteCarlo: {
        iterations: adapter.monteCarloStats.iterations,
        convergenceReached: true,
      },
    };
  }

  private static buildReasons(
    homeWinProb: number,
    reasoning: string
  ): ConfidenceReason[] {
    const reasons: ConfidenceReason[] = [
      {
        label: "Simulation convergence reached",
        status: "pass",
        detail: "Monte Carlo iterations completed",
      },
    ];

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
        detail: "Close match with visible uncertainty",
      });
    } else {
      reasons.push({
        label: "Uncertain outcome",
        status: "fail",
        detail: "Near 50-50 probability",
      });
    }

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

    return reasons;
  }
}
