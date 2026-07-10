import fs from "node:fs";
import path from "node:path";
import { Activity, DatabaseZap, Search, ShieldCheck, Trophy, UsersRound } from "lucide-react";
import { LocalizedText } from "@/components/LocalizedText";
import { loadSnapshotSync } from "@/lib/tournament/loader/snapshot.loader";
import type { TeamIntelligence } from "@/lib/tournament/types";

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
  intelligence?: TeamIntelligence;
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

function clampProbability(value: number) {
  return Math.max(0, Math.min(1, value));
}

function formatPercent(value: number) {
  return `${Math.round(clampProbability(value) * 100)}%`;
}

function buildTeamRows(): { rows: TeamRow[]; agentRun: AgentRun | null } {
  const snapshot = loadSnapshotSync();
  const agentRun = readLatestAgentRun();
  const agentTeams = agentRun?.state?.teams ?? {};
  const intelligenceByTeam = snapshot.team_intelligence ?? {};
  const rows: TeamRow[] = [];

  for (const [groupName, group] of Object.entries(snapshot.group_predictions)) {
    group.standings.forEach((standing, index) => {
      const agentTeam = agentTeams[standing.team] ?? {};
      const intelligence = intelligenceByTeam[standing.team];
      rows.push({
        name: standing.team,
        group: groupName,
        points: standing.points,
        goalDiff: standing.goal_diff,
        rank: index + 1,
        qualified: group.qualifiers.includes(standing.team),
        strength: intelligence ? intelligence.overall_strength / 100 : agentTeam.strength_score ?? 0,
        intelligence,
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
  label: React.ReactNode;
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
  const groups = Array.from(new Set(rows.map((row) => row.group))).sort();
  const qualifiedCount = rows.filter((row) => row.qualified).length;
  const profiledTeams = rows.filter((row) => row.intelligence).length;

  return (
    <main className="page-shell min-h-screen px-4 py-12 md:px-6">
      <section className="mx-auto w-full max-w-[1600px] min-w-0">
        <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-8 shadow-sm">
          <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            <div>
              <Search className="h-8 w-8 text-[color:var(--accent)]" />
              <h1 className="mt-6 text-4xl font-semibold"><LocalizedText en="Team intelligence" zh="球队实力画像" /></h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-[color:var(--muted)]">
                <LocalizedText
                  en="Explore the 48 projected teams through DataForAgent evidence, LLM-extracted tactical profiles, structured strengths and risks, plus the current tournament projection."
                  zh="基于 DataForAgent 赛前资料、LLM 提炼的战术画像、优势与风险，查看全部 48 支球队及当前赛事预测。"
                />
              </p>
            </div>
            <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface2)] p-4 md:min-w-64">
              <p className="text-xs text-[color:var(--muted)]"><LocalizedText en="Latest agent run" zh="最近一次 Agent 运行" /></p>
              <p className="mt-2 text-sm font-medium">{agentRun?.generated_at ?? <LocalizedText en="No run artifact found" zh="未找到运行记录" />}</p>
            </div>
          </div>
        </div>

        <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Metric icon={UsersRound} label={<LocalizedText en="Teams" zh="球队" />} value={rows.length} />
          <Metric icon={DatabaseZap} label={<LocalizedText en="Groups" zh="小组" />} value={groups.length} />
          <Metric icon={ShieldCheck} label={<LocalizedText en="Projected qualifiers" zh="预测晋级球队" />} value={qualifiedCount} />
          <Metric icon={Activity} label={<LocalizedText en="Squad players" zh="名单球员" />} value={squadStats?.total_players ?? 0} />
          <Metric icon={Trophy} label={<LocalizedText en="LLM profiles" zh="LLM 球队画像" />} value={`${profiledTeams}/48`} />
        </section>

        <section className="mt-6 min-w-0">
          <div className="min-w-0 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-5 md:p-6">
            <div className="flex items-center gap-3">
              <UsersRound className="h-5 w-5 text-[color:var(--accent)]" />
              <h2 className="text-xl font-semibold"><LocalizedText en="All teams" zh="全部球队" /></h2>
            </div>
            <div className="mt-5 max-w-full overflow-x-auto overscroll-contain">
              <table className="w-full min-w-[1120px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-[color:var(--border)] text-left text-xs text-[color:var(--muted)]">
                    <th className="py-3 pr-4 font-medium"><LocalizedText en="Team" zh="球队" /></th>
                    <th className="py-3 pr-4 font-medium"><LocalizedText en="Group" zh="小组" /></th>
                    <th className="py-3 pr-4 font-medium"><LocalizedText en="Rank" zh="排名" /></th>
                    <th className="py-3 pr-4 font-medium"><LocalizedText en="Points" zh="积分" /></th>
                    <th className="py-3 pr-4 font-medium"><LocalizedText en="GD" zh="净胜球" /></th>
                    <th className="py-3 pr-4 font-medium"><LocalizedText en="Strength" zh="实力" /></th>
                    <th className="py-3 pr-4 font-medium"><LocalizedText en="LLM team profile" zh="LLM 球队画像" /></th>
                    <th className="py-3 pr-4 font-medium"><LocalizedText en="Key players" zh="关键球员" /></th>
                    <th className="py-3 pr-4 font-medium"><LocalizedText en="Status" zh="预测结果" /></th>
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
                      <td className="max-w-xs py-3 pr-4">
                        {team.intelligence ? (
                          <div>
                            <p className="font-medium">{team.intelligence.tactical_profile}</p>
                            <p className="mt-1 text-xs leading-5 text-[color:var(--muted)]">{team.intelligence.summary}</p>
                          </div>
                        ) : (
                          <span className="text-[color:var(--muted)]"><LocalizedText en="Awaiting profile generation" zh="等待生成球队画像" /></span>
                        )}
                      </td>
                      <td className="max-w-[180px] py-3 pr-4 text-xs leading-5 text-[color:var(--muted)]">
                        {team.intelligence?.key_players.join(" · ") ?? "-"}
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={
                            team.qualified
                              ? "rounded-full bg-[rgba(63,185,80,0.14)] px-2.5 py-1 text-xs font-medium text-green"
                              : "rounded-full bg-[rgba(118,131,144,0.18)] px-2.5 py-1 text-xs font-medium text-[color:var(--muted)]"
                          }
                        >
                          {team.qualified ? <LocalizedText en="Projected through" zh="预测晋级" /> : <LocalizedText en="Group exit" zh="小组出局" />}
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
