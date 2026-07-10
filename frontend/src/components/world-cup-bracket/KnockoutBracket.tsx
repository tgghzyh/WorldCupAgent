"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { CountryFlag } from "@/components/world-cup-bracket/CountryFlag";
import { getStageName, useI18n } from "@/i18n";
import type { BracketMatch, BracketRound, GroupStanding } from "@/lib/world-cup-bracket/types";
import { MatchDetailDrawer } from "./MatchDetailDrawer";
import { MatchNode } from "./MatchNode";
import { ZoomPanCanvas } from "./ZoomPanCanvas";

type KnockoutBracketProps = {
  rounds: BracketRound[];
  bestThirdTeams: GroupStanding[];
};

const roundSpacing: Record<string, string> = {
  round_of_32: "gap-3",
  round_of_16: "gap-8 pt-8",
  quarter_final: "gap-20 pt-20",
  semi_final: "gap-44 pt-44",
  third_place: "gap-4 pt-8",
  final: "gap-4 pt-72",
};

export function KnockoutBracket({ rounds, bestThirdTeams }: KnockoutBracketProps) {
  const { locale, t } = useI18n();
  const [selectedMatch, setSelectedMatch] = React.useState<BracketMatch | null>(null);

  return (
    <section className="space-y-5">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-medium text-[color:var(--accent)]">{t("schedule.knockoutProjection")}</p>
          <h2 className="mt-2 text-2xl font-semibold text-[color:var(--text)]">
            {t("schedule.knockoutSubtitle")}
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {bestThirdTeams.map((row) => (
            <Badge key={row.team.id} className="bg-[rgba(10,102,194,0.08)] text-[color:var(--brand-blue)]">
              <CountryFlag team={row.team} className="h-3 w-[18px]" />
              {row.team.name} {t("schedule.bestThird")}
            </Badge>
          ))}
        </div>
      </div>

      <ZoomPanCanvas>
        <div className="flex min-w-[1780px] items-start gap-8 pb-8">
          {rounds.map((round) => (
            <div key={round.id} className="relative w-[270px] shrink-0">
              <div className="sticky left-0 top-0 mb-4 rounded-full border border-[color:var(--border)] bg-[rgba(255,251,244,0.92)] px-4 py-2 text-center text-sm font-semibold">
                {getStageName(round.title, locale)}
              </div>
              <div className={`flex flex-col ${roundSpacing[round.id] ?? "gap-6"}`}>
                {round.matches.map((match) => (
                  <div key={match.id} className="relative">
                    <MatchNode
                      match={match}
                      compact={round.id !== "round_of_32"}
                      onSelect={setSelectedMatch}
                    />
                    {round.id !== "final" && (
                      <span className="absolute left-full top-1/2 h-px w-8 bg-[rgba(117,107,94,0.34)]" />
                    )}
                    {round.id !== "round_of_32" && (
                      <span className="absolute right-full top-1/2 h-px w-8 bg-[rgba(117,107,94,0.34)]" />
                    )}
                    <p className="mt-1 max-w-[240px] text-[10px] leading-4 text-[color:var(--muted)]">
                      {locale === "zh"
                        ? `${match.winnerTeamId === match.home.team.id ? match.home.team.name : match.away.team.name} 预测晋级`
                        : match.advancementRule}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </ZoomPanCanvas>
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
