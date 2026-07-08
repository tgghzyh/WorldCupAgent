import fs from "node:fs";
import path from "node:path";
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";
import { AppChrome, PageIntro } from "@/components/AppChrome";
import { loadSnapshotSync } from "@/lib/tournament/loader/snapshot.loader";
import type { Snapshot } from "@/lib/tournament/types";

type CompareChange = {
  subject: string;
  before: string;
  after: string;
  delta: string;
  direction: "up" | "down" | "flat";
};

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function parsePercent(value: string): number {
  const parsed = Number.parseFloat(value.replace("%", ""));
  return Number.isNaN(parsed) ? 0 : parsed / 100;
}

function formatDelta(value: number, suffix = "pp"): string {
  if (Math.abs(value) < 0.001) return "0";
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(1)}${suffix}`;
}

function directionFromDelta(value: number): CompareChange["direction"] {
  if (value > 0.001) return "up";
  if (value < -0.001) return "down";
  return "flat";
}

function loadPreviousSnapshotSync(current: Snapshot): Snapshot {
  const snapshotsDir = path.resolve(process.cwd(), "..", "data", "snapshots");

  try {
    const candidates = fs
      .readdirSync(snapshotsDir)
      .filter((file) => file.endsWith(".json") && file !== "latest.json")
      .map((file) => path.join(snapshotsDir, file))
      .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);

    for (const candidate of candidates) {
      const data = JSON.parse(fs.readFileSync(candidate, "utf-8")) as Snapshot;
      if (data.prediction_version !== current.prediction_version || data.snapshot_time !== current.snapshot_time) {
        return data;
      }
      return data;
    }
  } catch {
    return current;
  }

  return current;
}

function firstGroupMatch(snapshot: Snapshot) {
  return Object.values(snapshot.group_predictions)[0]?.matches[0];
}

function buildCompareChanges(previous: Snapshot, current: Snapshot): CompareChange[] {
  const previousMatch = firstGroupMatch(previous);
  const currentMatch = firstGroupMatch(current);
  const championDelta = current.champion_probability - previous.champion_probability;
  const matchDelta =
    previousMatch && currentMatch
      ? parsePercent(currentMatch.home_win_prob) - parsePercent(previousMatch.home_win_prob)
      : 0;

  return [
    {
      subject: "Champion probability",
      before: `${previous.champion} ${formatPercent(previous.champion_probability)}`,
      after: `${current.champion} ${formatPercent(current.champion_probability)}`,
      delta: formatDelta(championDelta),
      direction: directionFromDelta(championDelta),
    },
    {
      subject: "Runner-up projection",
      before: previous.runner_up,
      after: current.runner_up,
      delta: previous.runner_up === current.runner_up ? "Same" : "Changed",
      direction: previous.runner_up === current.runner_up ? "flat" : "up",
    },
    {
      subject: "Third-place projection",
      before: previous.third_place,
      after: current.third_place,
      delta: previous.third_place === current.third_place ? "Same" : "Changed",
      direction: previous.third_place === current.third_place ? "flat" : "up",
    },
    {
      subject: previousMatch && currentMatch
        ? `${currentMatch.home_team} home-win probability`
        : "Featured match home-win probability",
      before: previousMatch ? previousMatch.home_win_prob : "n/a",
      after: currentMatch ? currentMatch.home_win_prob : "n/a",
      delta: formatDelta(matchDelta),
      direction: directionFromDelta(matchDelta),
    },
    {
      subject: "Monte Carlo simulations",
      before: previous.monte_carlo_simulations.toLocaleString(),
      after: current.monte_carlo_simulations.toLocaleString(),
      delta: `${current.monte_carlo_simulations - previous.monte_carlo_simulations}`,
      direction: directionFromDelta(current.monte_carlo_simulations - previous.monte_carlo_simulations),
    },
  ];
}

export default function ComparePage() {
  const current = loadSnapshotSync();
  const previous = loadPreviousSnapshotSync(current);
  const compareChanges = buildCompareChanges(previous, current);

  return (
    <AppChrome>
      <PageIntro
        eyebrow="Prediction movement"
        title="What changed since the last run?"
        description="A lightweight comparison view that proves the prediction product is alive: probabilities move, assumptions shift, and the Agent leaves a clear audit trail."
      />

      <section className="mx-auto max-w-5xl px-5 pb-16">
        <div className="glass-panel overflow-hidden rounded-[2rem]">
          {compareChanges.map((change, index) => {
            const isUp = change.direction === "up";
            const isFlat = change.direction === "flat";
            const Icon = isFlat ? ArrowRight : isUp ? ArrowUpRight : ArrowDownRight;
            return (
              <div
                key={change.subject}
                className={`grid gap-4 p-6 md:grid-cols-[1.3fr_0.7fr_0.7fr_0.5fr] ${
                  index > 0 ? "border-t hairline" : ""
                }`}
              >
                <div>
                  <p className="font-medium">{change.subject}</p>
                  <p className="mt-1 text-sm text-muted">Daily model comparison</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Before</p>
                  <p className="mt-1 text-xl font-semibold">{change.before}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">After</p>
                  <p className="mt-1 text-xl font-semibold">{change.after}</p>
                </div>
                <div className={isFlat ? "text-muted" : isUp ? "text-green" : "text-red"}>
                  <Icon className="h-5 w-5" />
                  <p className="mt-1 font-semibold">{change.delta}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </AppChrome>
  );
}
