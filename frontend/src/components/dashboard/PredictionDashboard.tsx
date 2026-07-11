"use client";

import * as React from "react";
import {
  ArrowRight,
  Braces,
  DatabaseZap,
  RefreshCw,
  Search,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CountryFlag } from "@/components/world-cup-bracket/CountryFlag";
import { useI18n } from "@/i18n";
import { cn } from "@/lib/utils";
import type { BracketMatch, Team, WorldCupBracketData } from "@/lib/world-cup-bracket/types";

type PredictionDashboardProps = {
  data: WorldCupBracketData;
};

function formatUpdateTime(value: string) {
  const date = new Date(value.replace(" UTC", "Z"));
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

function getFinalMatch(data: WorldCupBracketData): BracketMatch {
  const finalRound = data.rounds.find((round) => round.id === "final");
  return finalRound?.matches[0] ?? data.rounds[data.rounds.length - 1].matches[0];
}

function ChampionProgress({ probability, label }: { probability: number; label: string }) {
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - probability);

  return (
    <div className="relative grid h-40 w-40 place-items-center">
      <svg className="h-40 w-40 -rotate-90" viewBox="0 0 140 140" aria-hidden="true">
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="rgba(223,207,186,0.88)"
          strokeWidth="12"
        />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="url(#championGradient)"
          strokeLinecap="round"
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
        <defs>
          <linearGradient id="championGradient" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--brand-blue)" />
            <stop offset="55%" stopColor="var(--brand-green)" />
            <stop offset="100%" stopColor="var(--brand-gold)" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute text-center">
        <p className="text-4xl font-semibold tabular-nums">
          {Math.round(probability * 100)}%
        </p>
        <p className="mt-1 text-xs font-medium text-[color:var(--muted)]">{label}</p>
      </div>
    </div>
  );
}

function QuickNavCard({
  href,
  icon: Icon,
  title,
  text,
}: {
  href: string;
  icon: React.ElementType;
  title: string;
  text: string;
}) {
  return (
    <a
      href={href}
      className="group rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.86)] p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-[color:var(--accent)] hover:shadow-md"
    >
      <div className="flex items-center justify-between">
        <span className="grid h-10 w-10 place-items-center rounded-full bg-[rgba(10,102,194,0.10)] text-[color:var(--brand-blue)]">
          <Icon className="h-5 w-5" />
        </span>
        <ArrowRight className="h-4 w-4 text-[color:var(--muted)] transition group-hover:translate-x-1 group-hover:text-[color:var(--text)]" />
      </div>
      <h3 className="mt-5 text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">{text}</p>
    </a>
  );
}

export function PredictionDashboard({ data }: PredictionDashboardProps) {
  const { t, translations } = useI18n();
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [lastUpdated, setLastUpdated] = React.useState(data.generatedAt);
  const finalMatch = getFinalMatch(data);
  const championSlot =
    finalMatch.winnerTeamId === finalMatch.away.team.id ? finalMatch.away : finalMatch.home;
  const championTournamentProbability =
    data.titleContenders.find((entry) => entry.team.id === championSlot.team.id)?.probability ??
    championSlot.probability;
  const championName =
    (translations.teams as Record<string, string>)[championSlot.team.name] ??
    championSlot.team.name;
  const summaries = [
    t("dashboard.summary1", { team: championName }),
    t("dashboard.summary2"),
    t("dashboard.summary3"),
  ];

  function refresh() {
    setIsRefreshing(true);
    window.setTimeout(() => {
      setLastUpdated(new Date().toISOString());
      setIsRefreshing(false);
    }, 900);
  }

  return (
    <main className="min-h-screen bg-[color:var(--bg)] text-[color:var(--text)]">
      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-6 md:px-6 lg:grid-cols-[1fr_auto]">
        <div />
        <div className="flex items-center justify-end gap-3 rounded-full border border-[color:var(--border)] bg-[rgba(255,251,244,0.78)] px-3 py-2 text-sm text-[color:var(--muted)] shadow-sm">
          <span className={cn("h-2 w-2 rounded-full", isRefreshing ? "animate-pulse bg-[color:var(--brand-gold)]" : "bg-[color:var(--brand-green)]")} />
          <span>{t("dashboard.lastUpdated", { time: formatUpdateTime(lastUpdated) })}</span>
          <Button
            className="h-8 px-3"
            disabled={isRefreshing}
            onClick={refresh}
            aria-label={t("dashboard.refresh")}
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
            {isRefreshing ? t("dashboard.refreshing") : t("dashboard.refresh")}
          </Button>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-5 px-4 pb-12 md:px-6 lg:grid-cols-[1.25fr_0.75fr]">
        <Card className="grid gap-8 bg-[linear-gradient(135deg,rgba(255,251,244,0.97),rgba(244,234,219,0.92))] p-5 shadow-[0_24px_80px_rgba(79,58,34,0.10)] md:grid-cols-[1fr_auto] md:p-8 lg:col-span-2">
          <div>
            <div className="flex flex-wrap gap-2">
              <Badge className="border-[color:var(--brand-red)] bg-[rgba(197,48,48,0.08)] text-[color:var(--brand-red)]">
                {t("dashboard.championForecast")}
              </Badge>
              <Badge className="border-[color:var(--brand-blue)] bg-[rgba(10,102,194,0.08)] text-[color:var(--brand-blue)]">
                {t("dashboard.agentDashboard")}
              </Badge>
            </div>
            <h1 className="mt-6 max-w-4xl text-4xl font-semibold tracking-normal md:text-6xl">
              <CountryFlag team={championSlot.team} className="mr-3 h-7 w-10" />
              {t("dashboard.heroTitle", { team: championName })}
            </h1>
            <div className="mt-6 grid gap-3">
              {summaries.map((summary) => (
                <p key={summary} className="flex gap-3 text-base leading-7 text-[color:var(--muted)]">
                  <Sparkles className="mt-1 h-4 w-4 shrink-0 text-[color:var(--brand-gold)]" />
                  {summary}
                </p>
              ))}
            </div>
            <a
              href="/schedule"
<<<<<<< HEAD
className="mt-7 inline-flex items-center gap-2 rounded-full border border-[rgba(82,108,90,0.38)] bg-[color:var(--accent)] px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-[rgba(82,108,90,0.90)] hover:shadow-md"            >
=======
              className="mt-7 inline-flex items-center gap-2 rounded-full border border-[rgba(82,108,90,0.38)] bg-[color:var(--accent)] px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-[rgba(82,108,90,0.90)] hover:shadow-md"
            >
>>>>>>> 39a9eea (Update frontend)
              {t("dashboard.viewReasoning")}
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
          <div className="grid place-items-center rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.72)] p-6">
            <ChampionProgress probability={championTournamentProbability} label={t("dashboard.toWin")} />
            <p className="mt-3 text-center text-sm text-[color:var(--muted)]">
              {t("dashboard.overallTitleProbability")}
            </p>
          </div>
        </Card>

        <section className="grid gap-4 lg:col-span-2 lg:grid-cols-3">
          <QuickNavCard
        href="/schedule"
            icon={Braces}
        title={t("dashboard.scheduleTree")}
        text={t("dashboard.scheduleTreeText")}
          />
          <QuickNavCard
        href="/teams"
            icon={Search}
        title={t("dashboard.teamSearch")}
        text={t("dashboard.teamSearchText")}
          />
          <QuickNavCard
        href="/data"
            icon={DatabaseZap}
        title={t("dashboard.dataProvenance")}
        text={t("dashboard.dataProvenanceText")}
          />
        </section>
      </section>
    </main>
  );
}
