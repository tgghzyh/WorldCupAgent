import fs from "node:fs";
import path from "node:path";
import { Activity, DatabaseZap, Search, ShieldCheck, Trophy, UsersRound } from "lucide-react";
import { loadSnapshotSync } from "@/lib/tournament/loader/snapshot.loader";

type AgentTeam = {
  name?: string;
  group?: string;
  points?: number;
  goal_diff?: number;
  strength_score?: number;
};

type AgentRun = {
  generated_at?: string;
  state?: {
    teams?: Record<string, AgentTeam>;
    predictions?: {
      data_sources?: {
        squad_stats?: {
          groups?: number;
          teams?: number;
          total_players?: number;
        };
      };
      tournament?: {
        predicted_champion?: string;
      };
    };
  };
};

type TeamRow = {
  name: string;
  group: string;
  points: number;
  goalDiff: number;
  rank: number;
  qualified: boolean;
  strength: number;
  titleProbability: number;
};

function readLatestAgentRun(): AgentRun | null {
  const outputDir = path.resolve(process.cwd(), "..", "data", "multi_agent");
  try {
    const latest = fs
      .readdirSync(outputDir)
      .filter((file) => file.startsWith("multi_agent_output_") && file.endsWith(".json"))
      .map((file) => {
        const filePath = path.join(outputDir, file);
        return { filePath, mtime: fs.statSync(filePath).mtimeMs };
      })
      .sort((a, b) => b.mtime - a.mtime)[0];

    if (!latest) return null;
    return JSON.parse(fs.readFileSync(latest.filePath, "utf-8")) as AgentRun;
  } catch {
    return null;
  }
}

function parseProbability(raw: unknown): number {
  if (typeof raw === "number") return raw;
  if (typeof raw !== "string") return 0;
  const match = raw.match(/\(([\d.]+)%\)/);
  if (match) return Number(match[1]) / 100;
  if (raw.endsWith("%")) return Number(raw.replace("%", "")) / 100;
  return 0;
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function buildTeamRows(): { rows: TeamRow[]; agentRun: AgentRun | null } {
  const snapshot = loadSnapshotSync();
  const agentRun = readLatestAgentRun();
  const agentTeams = agentRun?.state?.teams ?? {};
  const titleProbabilities = snapshot.champion_probabilities ?? {};
  const rows: TeamRow[] = [];

  for (const [groupName, group] of Object.entries(snapshot.group_predictions)) {
    group.standings.forEach((standing, index) => {
      const agentTeam = agentTeams[standing.team] ?? {};
      rows.push({
        name: standing.team,
        group: groupName,
        points: standing.points,
        goalDiff: standing.goal_diff,
        rank: index + 1,
        qualified: group.qualifiers.includes(standing.team),
        strength: agentTeam.strength_score ?? 0,
        titleProbability: parseProbability(titleProbabilities[standing.team]),
      });
    });
  }

  rows.sort((a, b) => {
    if (b.strength !== a.strength) return b.strength - a.strength;
    if (b.points !== a.points) return b.points - a.points;
    return b.goalDiff - a.goalDiff;
  });

  return { rows, agentRun };
}

function Metric({
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

function StrengthBar({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-[color:var(--surface2)]">
        <div className="h-full rounded-full bg-[color:var(--accent)]" style={{ width: formatPercent(value) }} />
      </div>
      <span className="w-10 text-right font-mono text-xs text-[color:var(--muted)]">{formatPercent(value)}</span>
    </div>
  );
}

export default function TeamsPage() {
  const { rows, agentRun } = buildTeamRows();
  const squadStats = agentRun?.state?.predictions?.data_sources?.squad_stats;
  const champion = agentRun?.state?.predictions?.tournament?.predicted_champion ?? rows[0]?.name ?? "Unknown";
  const groups = Array.from(new Set(rows.map((row) => row.group))).sort();
  const qualifiedCount = rows.filter((row) => row.qualified).length;

  return (
    <main className="page-shell min-h-screen px-4 py-12 md:px-6">
      <section className="mx-auto max-w-7xl">
        <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-8 shadow-sm">
          <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            <div>
              <Search className="h-8 w-8 text-[color:var(--accent)]" />
              <h1 className="mt-6 text-4xl font-semibold">Team intelligence</h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-[color:var(--muted)]">
                Explore all 48 projected teams by group, qualification status, Agent strength score, and title
                probability from the current prediction snapshot.
              </p>
            </div>
            <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface2)] p-4 md:min-w-64">
              <p className="text-xs text-[color:var(--muted)]">Latest agent run</p>
              <p className="mt-2 text-sm font-medium">{agentRun?.generated_at ?? "No run artifact found"}</p>
            </div>
          </div>
        </div>

        <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Metric icon={UsersRound} label="Teams" value={rows.length} />
          <Metric icon={DatabaseZap} label="Groups" value={groups.length} />
          <Metric icon={ShieldCheck} label="Projected qualifiers" value={qualifiedCount} />
          <Metric icon={Activity} label="Squad players" value={squadStats?.total_players ?? 0} />
          <Metric icon={Trophy} label="Champion pick" value={champion} />
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-6">
            <div className="flex items-center gap-3">
              <Trophy className="h-5 w-5 text-gold" />
              <h2 className="text-xl font-semibold">Top contenders</h2>
            </div>
            <div className="mt-5 space-y-3">
              {rows.slice(0, 10).map((team, index) => (
                <article key={team.name} className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface2)] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs text-[color:var(--muted)]">#{index + 1} / Group {team.group}</p>
                      <h3 className="mt-1 text-lg font-semibold">{team.name}</h3>
                    </div>
                    <span className="rounded-full bg-[rgba(88,166,255,0.14)] px-3 py-1 text-xs font-medium text-[color:var(--accent)]">
                      {formatPercent(team.titleProbability)}
                    </span>
                  </div>
                  <div className="mt-4 flex items-center justify-between gap-4 text-sm">
                    <span className="text-[color:var(--muted)]">Strength</span>
                    <StrengthBar value={team.strength} />
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-6">
            <div className="flex items-center gap-3">
              <UsersRound className="h-5 w-5 text-[color:var(--accent)]" />
              <h2 className="text-xl font-semibold">All teams</h2>
            </div>
            <div className="mt-5 overflow-x-auto">
              <table className="w-full min-w-[780px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-[color:var(--border)] text-left text-xs text-[color:var(--muted)]">
                    <th className="py-3 pr-4 font-medium">Team</th>
                    <th className="py-3 pr-4 font-medium">Group</th>
                    <th className="py-3 pr-4 font-medium">Rank</th>
                    <th className="py-3 pr-4 font-medium">Points</th>
                    <th className="py-3 pr-4 font-medium">GD</th>
                    <th className="py-3 pr-4 font-medium">Strength</th>
                    <th className="py-3 pr-4 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((team) => (
                    <tr key={team.name} className="border-b border-[color:var(--border)] last:border-b-0">
                      <td className="py-3 pr-4 font-medium">{team.name}</td>
                      <td className="py-3 pr-4 text-[color:var(--muted)]">{team.group}</td>
                      <td className="py-3 pr-4 text-[color:var(--muted)]">{team.rank}</td>
                      <td className="py-3 pr-4 text-[color:var(--muted)]">{team.points}</td>
                      <td className="py-3 pr-4 text-[color:var(--muted)]">{team.goalDiff > 0 ? `+${team.goalDiff}` : team.goalDiff}</td>
                      <td className="py-3 pr-4">
                        <StrengthBar value={team.strength} />
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={
                            team.qualified
                              ? "rounded-full bg-[rgba(63,185,80,0.14)] px-2.5 py-1 text-xs font-medium text-green"
                              : "rounded-full bg-[rgba(118,131,144,0.18)] px-2.5 py-1 text-xs font-medium text-[color:var(--muted)]"
                          }
                        >
                          {team.qualified ? "Projected through" : "Group exit"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}
