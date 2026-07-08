"use client";

import * as React from "react";
import {
  ArrowRight,
  Braces,
  DatabaseZap,
  RefreshCw,
  Search,
  Sparkles,
  Trophy,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useI18n } from "@/i18n";
import { cn } from "@/lib/utils";
import type { BracketMatch, Team, WorldCupBracketData } from "@/lib/world-cup-bracket/types";

type PredictionDashboardProps = {
  data: WorldCupBracketData;
};

type RankedTeam = {
  team: Team;
  probability: number;
  advantages: string[];
};

function formatUpdateTime(value: string) {
  const date = new Date(value.replace(" UTC", "Z"));
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  }).format(date);
}

function collectRankings(data: WorldCupBracketData): RankedTeam[] {
  if (data.titleContenders.length > 0) {
    return data.titleContenders.map((entry, index) => ({
      team: entry.team,
      probability: entry.probability,
      advantages: [
        "Champion probability",
        index < 2 ? "stablePath" : "upsideRoute",
        entry.probability > 0.55 ? "highControl" : "knockoutResilience",
      ],
    }));
  }

  const map = new Map<string, RankedTeam>();

  function add(team: Team, probability: number, label: string) {
    const current = map.get(team.id);
    if (!current) {
      map.set(team.id, { team, probability, advantages: [label] });
      return;
    }
    current.probability = Math.max(current.probability, probability);
    if (!current.advantages.includes(label) && current.advantages.length < 3) {
      current.advantages.push(label);
    }
  }

  for (const round of data.rounds) {
    for (const match of round.matches) {
      add(match.home.team, match.home.probability, match.home.sourceSeed ?? round.title);
      add(match.away.team, match.away.probability, match.away.sourceSeed ?? round.title);
    }
  }

  return [...map.values()]
    .sort((a, b) => b.probability - a.probability)
    .slice(0, 5)
    .map((entry, index) => ({
      ...entry,
      advantages: [
        entry.advantages[0] ?? "Model edge",
        index < 2 ? "stablePath" : "upsideRoute",
        entry.probability > 0.55 ? "highControl" : "knockoutResilience",
      ],
    }));
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

function TopRankCard({
  item,
  rankLabel,
  translatedName,
}: {
  item: RankedTeam;
  index: number;
  rankLabel: string;
  translatedName: string;
}) {
  return (
    <Card className="min-w-[240px] bg-[rgba(255,251,244,0.86)] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs text-[color:var(--muted)]">{rankLabel}</p>
          <h3 className="mt-2 truncate text-lg font-semibold">
            <span className="mr-2 text-xl">{item.team.flag}</span>
            {translatedName}
          </h3>
        </div>
        <p className="rounded-full bg-[rgba(10,102,194,0.10)] px-3 py-1 text-sm font-semibold text-[color:var(--brand-blue)]">
          {Math.round(item.probability * 100)}%
        </p>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-[color:var(--surface2)]">
        <div
          className="h-full rounded-full bg-[linear-gradient(90deg,var(--brand-blue),var(--brand-green))]"
          style={{ width: `${Math.round(item.probability * 100)}%` }}
        />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {item.advantages.map((advantage) => (
          <Badge key={advantage} className="border-transparent bg-[rgba(82,108,90,0.10)] text-[color:var(--accent)]">
            {advantage}
          </Badge>
        ))}
      </div>
    </Card>
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
  const rankings = collectRankings(data);
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
            aria-label="Refresh prediction data"
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
              <span className="mr-3">{championSlot.team.flag}</span>
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
              className="mt-7 inline-flex items-center gap-2 rounded-full border border-[rgba(10,102,194,0.22)] bg-[color:var(--brand-blue)] px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-[rgba(10,102,194,0.88)] hover:shadow-md"
            >
              {t("dashboard.viewReasoning")}
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
          <div className="grid place-items-center rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.72)] p-6">
            <ChampionProgress probability={championSlot.probability} label={t("dashboard.toWin")} />
            <p className="mt-3 text-center text-sm text-[color:var(--muted)]">
              {t("dashboard.finalBranch")}
            </p>
          </div>
        </Card>

        <Card className="p-5 lg:col-span-2">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-[color:var(--accent)]">{t("dashboard.top5Eyebrow")}</p>
              <h2 className="mt-1 text-2xl font-semibold">{t("dashboard.titleContenders")}</h2>
            </div>
            <Trophy className="h-6 w-6 text-[color:var(--gold)]" />
          </div>
          <div className="flex gap-4 overflow-x-auto pb-2">
            {rankings.map((item, index) => (
              <TopRankCard
                key={item.team.id}
                item={{
                  ...item,
                  advantages: item.advantages.map((advantage) =>
                    advantage in translations.dashboard
                      ? t(`dashboard.${advantage}`)
                      : advantage
                  ),
                }}
                index={index}
                rankLabel={t("dashboard.rank", { rank: index + 1 })}
                translatedName={(translations.teams as Record<string, string>)[item.team.name] ?? item.team.name}
              />
            ))}
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
