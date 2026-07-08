import fs from "node:fs";
import path from "node:path";
import type React from "react";
import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  DatabaseZap,
  FileClock,
  Route,
  ShieldCheck,
  Trophy,
} from "lucide-react";

type AgentTrace = {
  agent?: string;
  task?: string;
  status?: string;
  duration_ms?: number;
  steps?: unknown[];
};

type AgentRun = {
  generated_at?: string;
  tournament?: string;
  quality_score?: number;
  state?: {
    teams?: Record<string, { group?: string; points?: number; goal_diff?: number; strength_score?: number }>;
    predictions?: {
      data_sources?: {
        datasets?: string[];
        worldcup_matches?: number;
        league_matches?: number;
        squad_stats?: {
          groups?: number;
          teams?: number;
          total_players?: number;
        };
        snapshot_time?: string;
      };
      tournament?: {
        predicted_champion?: string;
        champion_probability?: number;
        champion_probabilities?: Record<string, number>;
        source_snapshot?: string;
      };
      explanation?: string;
      quality?: {
        score?: number;
        checks?: Record<string, boolean>;
      };
    };
    agent_traces?: AgentTrace[];
    warnings?: string[];
    errors?: string[];
    monte_carlo_runs?: number;
  };
};

function readLatestAgentRun(): { run: AgentRun | null; filename: string | null; error: string | null } {
  const outputDir = path.resolve(process.cwd(), "..", "data", "multi_agent");
  try {
    const files = fs
      .readdirSync(outputDir)
      .filter((file) => file.startsWith("multi_agent_output_") && file.endsWith(".json"))
      .map((file) => {
        const filePath = path.join(outputDir, file);
        return { file, filePath, mtime: fs.statSync(filePath).mtimeMs };
      })
      .sort((a, b) => b.mtime - a.mtime);

    if (!files[0]) {
      return { run: null, filename: null, error: "No multi-agent output file found." };
    }

    const run = JSON.parse(fs.readFileSync(files[0].filePath, "utf-8")) as AgentRun;
    return { run, filename: files[0].file, error: null };
  } catch (error) {
    return {
      run: null,
      filename: null,
      error: error instanceof Error ? error.message : "Unknown agent run error",
    };
  }
}

function pct(value: number | undefined) {
  return `${Math.round((value ?? 0) * 100)}%`;
}

function Stat({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-[color:var(--muted)]">{label}</p>
        <Icon className="h-4 w-4 text-[color:var(--accent)]" />
      </div>
      <p className="mt-3 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function StatusPill({ ok }: { ok: boolean }) {
  return (
    <span
      className={
        ok
          ? "rounded-full bg-[rgba(63,185,80,0.14)] px-2.5 py-1 text-xs font-medium text-green"
          : "rounded-full bg-[rgba(248,81,73,0.14)] px-2.5 py-1 text-xs font-medium text-red"
      }
    >
      {ok ? "pass" : "check"}
    </span>
  );
}

export default function AgentPage() {
  const { run, filename, error } = readLatestAgentRun();

  if (!run) {
    return (
      <main className="page-shell min-h-screen px-4 py-12 md:px-6">
        <section className="mx-auto max-w-5xl rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-8">
          <BrainCircuit className="h-8 w-8 text-red" />
          <h1 className="mt-6 text-3xl font-semibold">Agent run unavailable</h1>
          <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">{error}</p>
        </section>
      </main>
    );
  }

  const state = run.state ?? {};
  const predictions = state.predictions ?? {};
  const dataSources = predictions.data_sources ?? {};
  const tournament = predictions.tournament ?? {};
  const quality = predictions.quality ?? {};
  const traces = state.agent_traces ?? [];
  const teams = state.teams ?? {};
  const topTeams = Object.entries(teams)
    .sort(([, a], [, b]) => (b.strength_score ?? 0) - (a.strength_score ?? 0))
    .slice(0, 8);
  const checks = Object.entries(quality.checks ?? {});

  return (
    <main className="page-shell min-h-screen px-4 py-12 md:px-6">
      <section className="mx-auto max-w-7xl">
        <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-8 shadow-sm">
          <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <BrainCircuit className="h-8 w-8 text-[color:var(--accent)]" />
                <span className="rounded-full border border-[color:var(--border)] px-3 py-1 text-xs text-[color:var(--muted)]">
                  {filename}
                </span>
              </div>
              <h1 className="mt-6 text-4xl font-semibold">Multi-agent run</h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-[color:var(--muted)]">
                Latest pipeline execution from DataForAgent inputs through shared agent state, tournament
                summary, explanation, and quality checks.
              </p>
            </div>
            <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface2)] p-4 md:min-w-64">
              <p className="text-xs text-[color:var(--muted)]">Generated</p>
              <p className="mt-2 text-sm font-medium">{run.generated_at ?? "unknown"}</p>
            </div>
          </div>
        </div>

        <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat icon={ShieldCheck} label="Quality score" value={pct(run.quality_score)} />
          <Stat icon={DatabaseZap} label="Teams loaded" value={Object.keys(teams).length} />
          <Stat icon={Activity} label="Agent steps" value={traces.length} />
          <Stat icon={Trophy} label="Champion pick" value={tournament.predicted_champion ?? "unknown"} />
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-6">
            <div className="flex items-center gap-3">
              <Trophy className="h-5 w-5 text-gold" />
              <h2 className="text-xl font-semibold">Tournament summary</h2>
            </div>
            <p className="mt-4 text-5xl font-semibold">{tournament.predicted_champion ?? "Unknown"}</p>
            <p className="mt-2 text-sm text-[color:var(--muted)]">
              Champion probability {pct(tournament.champion_probability)} from {state.monte_carlo_runs ?? 0} simulation
              runs.
            </p>
            <p className="mt-5 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface2)] p-4 text-sm leading-6 text-[color:var(--muted)]">
              {predictions.explanation ?? "No explanation generated."}
            </p>
          </div>

          <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-6">
            <div className="flex items-center gap-3">
              <DatabaseZap className="h-5 w-5 text-green" />
              <h2 className="text-xl font-semibold">Data coverage</h2>
            </div>
            <div className="mt-5 grid gap-3">
              <Stat icon={FileClock} label="World Cup historical matches" value={dataSources.worldcup_matches ?? 0} />
              <Stat icon={FileClock} label="League matches" value={dataSources.league_matches ?? 0} />
              <Stat icon={DatabaseZap} label="Squad players" value={dataSources.squad_stats?.total_players ?? 0} />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {(dataSources.datasets ?? []).map((dataset) => (
                <span key={dataset} className="rounded-full bg-[color:var(--surface2)] px-3 py-1 text-xs text-[color:var(--muted)]">
                  {dataset}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-6">
            <div className="flex items-center gap-3">
              <Route className="h-5 w-5 text-[color:var(--accent)]" />
              <h2 className="text-xl font-semibold">Agent trace</h2>
            </div>
            <div className="mt-5 space-y-3">
              {traces.map((trace, index) => (
                <article key={`${trace.agent}-${index}`} className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface2)] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{trace.agent ?? `agent_${index + 1}`}</p>
                      <p className="mt-1 text-xs text-[color:var(--muted)]">{trace.task}</p>
                    </div>
                    <StatusPill ok={trace.status === "success"} />
                  </div>
                  <p className="mt-3 text-xs text-[color:var(--muted)]">
                    {trace.steps?.length ?? 0} ReAct steps / {Math.round(trace.duration_ms ?? 0)}ms
                  </p>
                </article>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-6">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-green" />
              <h2 className="text-xl font-semibold">Quality checks</h2>
            </div>
            <div className="mt-5 space-y-3">
              {checks.map(([name, ok]) => (
                <div key={name} className="flex items-center justify-between gap-3 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface2)] p-4">
                  <span className="text-sm">{name.replaceAll("_", " ")}</span>
                  <StatusPill ok={ok} />
                </div>
              ))}
            </div>

            <div className="mt-6">
              <h3 className="text-sm font-semibold text-[color:var(--muted)]">Top strength scores</h3>
              <div className="mt-3 space-y-2">
                {topTeams.map(([team, data]) => (
                  <div key={team} className="grid grid-cols-[1fr_auto] items-center gap-3 text-sm">
                    <span>{team}</span>
                    <span className="font-mono text-[color:var(--muted)]">{pct(data.strength_score)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}
