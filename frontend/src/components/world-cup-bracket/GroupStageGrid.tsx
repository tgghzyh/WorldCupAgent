"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useI18n } from "@/i18n";
import type { BracketMatch, GroupStageGroup, QualificationRule } from "@/lib/world-cup-bracket/types";
import { MatchDetailDrawer } from "./MatchDetailDrawer";

type GroupStageGridProps = {
  groups: GroupStageGroup[];
  qualificationRules: QualificationRule[];
};

function qualificationLabel(value?: string) {
  if (value === "winner") return "1st";
  if (value === "runner_up") return "2nd";
  if (value === "best_third") return "Best 3rd";
  return "";
}

export function GroupStageGrid({ groups, qualificationRules }: GroupStageGridProps) {
  const { t } = useI18n();
  const [selectedMatch, setSelectedMatch] = React.useState<BracketMatch | null>(null);

  return (
    <section className="space-y-5">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-medium text-[color:var(--accent)]">{t("schedule.groupStage")}</p>
          <h2 className="mt-2 text-2xl font-semibold text-[color:var(--text)]">
            {t("schedule.groupSubtitle")}
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {qualificationRules.map((rule) => (
            <Badge key={rule.slot} className="bg-[color:var(--surface)]">
              {rule.slot}: {rule.description}
            </Badge>
          ))}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {groups.map((group) => (
          <Card key={group.id} className="overflow-hidden bg-[rgba(255,251,244,0.86)]">
            <CardHeader className="flex flex-row items-center justify-between border-b border-[color:var(--border)]">
              <h3 className="text-base font-semibold">{group.name}</h3>
              <Badge>{group.standings.filter((row) => row.qualifiedAs).length} {t("schedule.through")}</Badge>
            </CardHeader>
            <CardContent className="p-0">
              <div className="grid grid-cols-[2rem_1fr_2.5rem_2.5rem_2.5rem] px-3 py-2 text-xs font-medium text-[color:var(--muted)]">
                <span>#</span>
                <span>{t("schedule.team")}</span>
                <span className="text-right">Pts</span>
                <span className="text-right">GD</span>
                <span className="text-right">{t("schedule.seed")}</span>
              </div>
              {group.standings.map((row) => (
                <div
                  key={row.team.id}
                  className="grid grid-cols-[2rem_1fr_2.5rem_2.5rem_2.5rem] items-center border-t border-[rgba(226,212,193,0.55)] px-3 py-2 text-sm"
                >
                  <span className="text-[color:var(--muted)]">{row.rank}</span>
                  <span className="flex min-w-0 items-center gap-2">
                    <span className="text-lg leading-none">{row.team.flag}</span>
                    <span className="truncate font-medium">{row.team.name}</span>
                  </span>
                  <span className="text-right font-semibold">{row.points}</span>
                  <span className="text-right text-[color:var(--muted)]">{row.goalDiff > 0 ? `+${row.goalDiff}` : row.goalDiff}</span>
                  <span className="text-right text-[10px] font-medium text-[color:var(--accent)]">
                    {qualificationLabel(row.qualifiedAs)}
                  </span>
                </div>
              ))}
              <div className="border-t border-[color:var(--border)] p-3">
                <p className="mb-2 text-xs font-medium uppercase tracking-normal text-[color:var(--muted)]">
                  Match predictions
                </p>
                <div className="grid gap-2">
                  {(group.matches ?? []).map((match) => (
                    <button
                      key={match.id}
                      type="button"
                      className="grid grid-cols-[1fr_auto] items-center gap-3 rounded-md border border-[rgba(226,212,193,0.75)] bg-[rgba(255,251,244,0.62)] px-3 py-2 text-left transition hover:border-[color:var(--accent)] hover:bg-[rgba(255,251,244,0.92)]"
                      onClick={() => setSelectedMatch(match)}
                    >
                      <span className="min-w-0 truncate text-xs">
                        {match.home.team.flag} {match.home.team.name}
                        <span className="px-1 text-[color:var(--muted)]">vs</span>
                        {match.away.team.flag} {match.away.team.name}
                      </span>
                      <span className="font-mono text-xs font-semibold">
                        {match.predictedScore ?? "TBD"}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      <MatchDetailDrawer
        match={selectedMatch}
        open={selectedMatch !== null}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setSelectedMatch(null);
          }
        }}
      />
    </section>
  );
}
