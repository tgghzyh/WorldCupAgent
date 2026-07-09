"use client";

import * as React from "react";
import {
  Activity,
  Dumbbell,
  ExternalLink,
  HeartPulse,
  Home,
  ShieldAlert,
  Swords,
  Timer,
  X,
  Zap,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useI18n } from "@/i18n";
import { cn } from "@/lib/utils";
import type { BracketMatch, ReasoningFactor } from "@/lib/world-cup-bracket/types";

type MatchDetailDrawerProps = {
  match: BracketMatch | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const factorIcons: Record<ReasoningFactor["type"], React.ElementType> = {
  fitness: Dumbbell,
  tactical: Swords,
  injury: HeartPulse,
  home: Home,
  form: Activity,
  transition: Zap,
};

const confidenceTone = {
  high: "border-[color:var(--brand-green)] bg-[rgba(7,132,95,0.10)] text-[color:var(--brand-green)]",
  medium: "border-[color:var(--brand-gold)] bg-[rgba(214,162,30,0.12)] text-[color:var(--brand-gold)]",
  low: "border-[color:var(--brand-red)] bg-[rgba(197,48,48,0.10)] text-[color:var(--brand-red)]",
};

function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes} UTC`;
}

function FactorCard({
  factor,
  contributionLabel,
}: {
  factor: ReasoningFactor;
  contributionLabel: string;
}) {
  const Icon = factorIcons[factor.type] ?? ShieldAlert;
  return (
    <Card className="bg-[rgba(255,251,244,0.82)] p-4">
      <div className="flex gap-3">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[rgba(82,108,90,0.12)] text-[color:var(--accent)]">
          <Icon className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <Badge className="border-transparent bg-[rgba(10,102,194,0.08)] text-[color:var(--brand-blue)]">
            {factor.label}
          </Badge>
          <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">
            {factor.description}
          </p>
          <div className="mt-4">
            <div className="mb-1 flex items-center justify-between text-xs text-[color:var(--muted)]">
              <span>{contributionLabel}</span>
              <span>{Math.round(factor.weight * 100)}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-[color:var(--surface2)]">
              <div
                className="h-full rounded-full bg-[linear-gradient(90deg,var(--brand-blue),var(--brand-green))]"
                style={{ width: `${Math.round(factor.weight * 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

export function MatchDetailDrawer({ match, open, onOpenChange }: MatchDetailDrawerProps) {
  const { t } = useI18n();
  const closeButtonRef = React.useRef<HTMLButtonElement>(null);
  const titleId = React.useId();
  const descriptionId = React.useId();

  React.useEffect(() => {
    if (!open) return;

    closeButtonRef.current?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onOpenChange(false);
      }
    }

    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onOpenChange]);

  if (!open || !match) {
    return null;
  }

  const score = match.actualScore ?? match.predictedScore ?? "TBD";
  const detail = match.detail;
  const chartData = detail.metricComparison.map((metric) => ({
    name: metric.label,
    [match.home.team.code]: metric.homeValue,
    [match.away.team.code]: metric.awayValue,
    unit: metric.unit,
  }));

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        aria-label="Close match detail overlay"
              className="absolute inset-0 cursor-default bg-[rgba(39,35,31,0.34)] backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      <aside
        data-testid="match-detail-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        className="absolute bottom-0 right-0 top-auto flex max-h-[92vh] w-full flex-col rounded-t-lg border border-[color:var(--border)] bg-[color:var(--surface)] shadow-[0_-24px_90px_rgba(39,35,31,0.22)] outline-none md:bottom-4 md:right-4 md:top-4 md:max-h-none md:w-[720px] md:rounded-lg"
      >
        <header className="border-b border-[color:var(--border)] p-4 md:p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p id={descriptionId} className="text-sm text-[color:var(--muted)]">
                {match.label} · {match.kickoffLabel}
              </p>
              <h2 id={titleId} className="mt-2 text-2xl font-semibold text-[color:var(--text)]">
                {match.home.team.flag} {match.home.team.name}
                <span className="px-2 text-[color:var(--muted)]">vs</span>
                {match.away.team.flag} {match.away.team.name}
              </h2>
            </div>
            <Button
              ref={closeButtonRef}
              className="h-9 w-9 shrink-0 bg-[color:var(--surface2)] p-0 text-[color:var(--text)]"
              aria-label={t("drawer.close")}
              onClick={() => onOpenChange(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-[1fr_auto_1fr] sm:items-center">
            <div className="rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.78)] p-3">
              <p className="text-xs text-[color:var(--muted)]">{t("drawer.home")}</p>
              <p className="mt-1 text-lg font-semibold">
                {match.home.team.flag} {match.home.team.name}
              </p>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                {t("drawer.winProbability", { value: Math.round(match.home.probability * 100) })}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-[color:var(--muted)]">
                {match.actualScore ? t("drawer.actualScore") : t("drawer.predictedScore")}
              </p>
              <p className="mt-1 font-mono text-4xl font-semibold text-[color:var(--text)]">
                {score}
              </p>
              <Badge className={cn("mt-2", confidenceTone[detail.confidence])}>
                {t(`drawer.${detail.confidence}`)}
              </Badge>
            </div>
            <div className="rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.78)] p-3 sm:text-right">
              <p className="text-xs text-[color:var(--muted)]">{t("drawer.away")}</p>
              <p className="mt-1 text-lg font-semibold">
                {match.away.team.flag} {match.away.team.name}
              </p>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                {t("drawer.winProbability", { value: Math.round(match.away.probability * 100) })}
              </p>
            </div>
          </div>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto p-4 md:p-5">
          {detail.summary && (
            <section className="mb-6">
              <div className="mb-3 flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-[color:var(--accent)]" />
                <h3 className="text-base font-semibold">{t("drawer.reasoningSummary")}</h3>
              </div>
              <Card className="bg-[rgba(255,251,244,0.82)] p-4">
                <p className="text-sm leading-6 text-[color:var(--muted)]">{detail.summary}</p>
              </Card>
            </section>
          )}

          <section>
            <div className="mb-3 flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-[color:var(--accent)]" />
              <h3 className="text-base font-semibold">{t("drawer.reasoningFactors")}</h3>
            </div>
            <div className="grid gap-3">
              {detail.reasoningFactors.map((factor) => (
                <FactorCard
                  key={factor.id}
                  factor={factor}
                  contributionLabel={t("drawer.contributionWeight")}
                />
              ))}
            </div>
          </section>

          <section className="mt-6">
            <div className="mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-[color:var(--accent)]" />
              <h3 className="text-base font-semibold">{t("drawer.dataComparison")}</h3>
            </div>
            <Card className="h-[320px] bg-[rgba(255,251,244,0.82)] p-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
                  <CartesianGrid stroke="rgba(117,107,94,0.18)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: "var(--muted)", fontSize: 12 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: "var(--muted)", fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip
                    cursor={{ fill: "rgba(82,108,90,0.08)" }}
                    contentStyle={{
                      borderRadius: 8,
                      borderColor: "var(--border)",
                      background: "var(--surface)",
                      color: "var(--text)",
                    }}
                  />
                  <Bar dataKey={match.home.team.code} fill="var(--brand-blue)" radius={[6, 6, 0, 0]} />
                  <Bar dataKey={match.away.team.code} fill="var(--brand-red)" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </section>
        </div>

        <footer className="border-t border-[color:var(--border)] p-4 md:p-5">
          <div className="flex flex-col gap-3 text-sm text-[color:var(--muted)] md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap gap-3">
              {detail.dataSources.map((source) => (
                <a
                  key={source.href}
                  href={source.href}
                  target={source.href.startsWith("http") ? "_blank" : undefined}
                  rel={source.href.startsWith("http") ? "noreferrer" : undefined}
                  className="inline-flex items-center gap-1 rounded-full border border-[color:var(--border)] px-3 py-1 transition hover:border-[color:var(--accent)] hover:text-[color:var(--text)]"
                >
                  {source.label}
                  <ExternalLink className="h-3 w-3" />
                </a>
              ))}
            </div>
            <div className="inline-flex items-center gap-2">
              <Timer className="h-4 w-4" />
              {t("drawer.agentReasoning", { time: formatTimestamp(detail.agentTimestamp) })}
            </div>
          </div>
        </footer>
      </aside>
    </div>
  );
}
