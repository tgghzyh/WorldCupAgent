import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import { ArrowRight, BrainCircuit, DatabaseZap, FileCheck2, MonitorUp } from "lucide-react";
import { LocalizedText } from "@/components/LocalizedText";
import { loadSnapshotSync } from "@/lib/tournament/loader/snapshot.loader";

type JsonStatus =
  | { ok: true; data: Record<string, unknown> }
  | { ok: false; error: string };

function readJsonStatus(filePath: string): JsonStatus {
  try {
    return {
      ok: true,
      data: JSON.parse(fs.readFileSync(filePath, "utf-8")) as Record<string, unknown>,
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Unknown JSON error",
    };
  }
}

function StatusCard({
  title,
  status,
  detail,
  isHealthy,
  icon: Icon,
}: {
  title: React.ReactNode;
  status: React.ReactNode;
  detail: React.ReactNode;
  isHealthy: boolean;
  icon: React.ElementType;
}) {
  return (
    <article className="rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.82)] p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[rgba(10,102,194,0.10)] text-[color:var(--brand-blue)]">
          <Icon className="h-5 w-5" />
        </span>
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className={isHealthy ? "mt-1 text-sm font-medium text-green" : "mt-1 text-sm font-medium text-red"}>
            {status}
          </p>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-[color:var(--muted)]">{detail}</p>
    </article>
  );
}

function Metric({
  label,
  value,
}: {
  label: React.ReactNode;
  value: string | number;
}) {
  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
      <p className="text-2xl font-semibold">{value}</p>
      <p className="mt-1 text-xs text-[color:var(--muted)]">{label}</p>
    </div>
  );
}

export default function DataPage() {
  const snapshot = loadSnapshotSync();
  const dataForAgentIndexPath = path.resolve(process.cwd(), "..", "DataForAgent", "data", "processed", "index.json");
  const rootSnapshotPath = path.resolve(process.cwd(), "..", "data", "snapshots", "latest.json");
  const dataForAgentIndex = readJsonStatus(dataForAgentIndexPath);
  const rootSnapshot = readJsonStatus(rootSnapshotPath);
  const groupCount = Object.keys(snapshot.group_predictions).length;
  const groupMatchCount = Object.values(snapshot.group_predictions).reduce(
    (total, group) => total + group.matches.length,
    0
  );
  const knockoutRounds = snapshot.knockout_predictions.rounds;
  const knockoutMatchCount =
    (knockoutRounds.round_of_32?.length ?? 0) +
    knockoutRounds.round_of_16.length +
    knockoutRounds.quarter_finals.length +
    knockoutRounds.semi_finals.length +
    2;

  return (
    <main className="page-shell min-h-screen px-4 py-12 md:px-6">
      <section className="mx-auto max-w-6xl">
        <div className="rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.86)] p-8 shadow-sm">
          <DatabaseZap className="h-8 w-8 text-[color:var(--brand-green)]" />
          <h1 className="mt-6 text-4xl font-semibold"><LocalizedText en="Data pipeline status" zh="数据管线状态" /></h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-[color:var(--muted)]">
            <LocalizedText en="This page shows how upstream pre-tournament data, Agent predictions, and the frontend public snapshot fit together." zh="这里展示赛前上游数据、Agent 预测结果与前端公开快照之间的衔接关系。" />
          </p>
        </div>

        <section className="mt-6 grid gap-4 lg:grid-cols-3">
          <StatusCard
            icon={DatabaseZap}
            isHealthy={dataForAgentIndex.ok}
            title="DataForAgent"
            status={<LocalizedText en={dataForAgentIndex.ok ? "Ready" : "Index needs repair"} zh={dataForAgentIndex.ok ? "就绪" : "索引需要修复"} />}
            detail={
              dataForAgentIndex.ok
                ? <LocalizedText en="Processed upstream datasets are indexed for model consumption." zh="已处理的上游数据集已建立索引，可供模型使用。" />
                : <LocalizedText en={`The processed index exists but is not valid JSON yet: ${dataForAgentIndex.error}`} zh={`已处理索引存在，但 JSON 格式无效：${dataForAgentIndex.error}`} />
            }
          />
          <StatusCard
            icon={BrainCircuit}
            isHealthy={rootSnapshot.ok}
            title="worldcup_agent"
            status={<LocalizedText en={rootSnapshot.ok ? "Ready" : "Snapshot needs repair"} zh={rootSnapshot.ok ? "就绪" : "快照需要修复"} />}
            detail={
              rootSnapshot.ok
                ? <LocalizedText en="The prediction system has produced a root latest.json snapshot." zh="预测系统已生成根目录 latest.json 快照。" />
                : <LocalizedText en={`The root prediction snapshot could not be parsed: ${rootSnapshot.error}`} zh={`无法解析根目录预测快照：${rootSnapshot.error}`} />
            }
          />
          <StatusCard
            icon={MonitorUp}
            isHealthy
            title="frontend"
            status={<LocalizedText en="Synced" zh="已同步" />}
            detail={<LocalizedText en="The frontend is reading frontend/public/data/snapshots/latest.json during static rendering." zh="前端静态渲染时读取 frontend/public/data/snapshots/latest.json。" />}
          />
        </section>

        <section className="mt-6 rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.82)] p-6">
          <div className="flex items-center gap-3">
            <FileCheck2 className="h-5 w-5 text-[color:var(--brand-green)]" />
            <div>
              <h2 className="text-xl font-semibold"><LocalizedText en="Current prediction snapshot" zh="当前预测快照" /></h2>
              <p className="text-sm text-[color:var(--muted)]">
                {snapshot.prediction_version} / {snapshot.snapshot_time}
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Metric label={<LocalizedText en="Champion" zh="冠军预测" />} value={snapshot.champion} />
            <Metric label={<LocalizedText en="Champion probability" zh="冠军概率" />} value={`${Math.round(snapshot.champion_probability * 100)}%`} />
            <Metric label={<LocalizedText en="Groups" zh="小组数" />} value={groupCount} />
            <Metric label={<LocalizedText en="Group matches" zh="小组赛场次" />} value={groupMatchCount} />
            <Metric label={<LocalizedText en="Knockout matches" zh="淘汰赛场次" />} value={knockoutMatchCount} />
          </div>

          <div className="mt-5 flex flex-col gap-3 rounded-lg border border-dashed border-[color:var(--border)] bg-[color:var(--surface)] p-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm leading-6 text-[color:var(--muted)]">
              <LocalizedText en="The multi-agent pipeline now consumes DataForAgent processed outputs and records a run artifact under data/multi_agent." zh="multi-agent 管线读取 DataForAgent 处理结果，并在 data/multi_agent 下记录运行产物。" />
            </p>
            <Link
              href="/agent"
              className="inline-flex shrink-0 items-center gap-2 rounded-full border border-[color:var(--border)] px-4 py-2 text-sm font-medium text-[color:var(--text)] transition hover:bg-[color:var(--surface2)]"
            >
              <LocalizedText en="View agent run" zh="查看 Agent 运行记录" />
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </section>
    </main>
  );
}
