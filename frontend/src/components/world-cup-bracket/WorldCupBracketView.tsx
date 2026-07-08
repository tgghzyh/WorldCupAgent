"use client";

import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/i18n";
import type { WorldCupBracketData } from "@/lib/world-cup-bracket/types";
import { GroupStageGrid } from "./GroupStageGrid";
import { KnockoutBracket } from "./KnockoutBracket";

type WorldCupBracketViewProps = {
  data: WorldCupBracketData;
  showIntro?: boolean;
};

export function WorldCupBracketView({ data, showIntro = true }: WorldCupBracketViewProps) {
  const { t } = useI18n();

  return (
    <div className="bg-[color:var(--bg)] text-[color:var(--text)]">
      {showIntro && (
        <section className="mx-auto max-w-7xl px-4 pb-8 pt-8 md:px-6 md:pt-12">
          <div className="rounded-lg border border-[color:var(--border)] bg-[linear-gradient(135deg,rgba(255,251,244,0.96),rgba(244,234,219,0.92))] p-5 shadow-[0_24px_80px_rgba(79,58,34,0.10)] md:p-8">
            <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
              <div>
                <div className="flex flex-wrap gap-2">
                  <Badge className="border-[color:var(--brand-red)] bg-[rgba(197,48,48,0.08)] text-[color:var(--brand-red)]">
                    Champion Agent
                  </Badge>
                  <Badge className="border-[color:var(--brand-blue)] bg-[rgba(10,102,194,0.08)] text-[color:var(--brand-blue)]">
                    Props-driven UI
                  </Badge>
                </div>
                <h1 className="mt-5 max-w-4xl text-4xl font-semibold tracking-normal md:text-6xl">
                  {t("schedule.title")}
                </h1>
                <p className="mt-5 max-w-2xl text-base leading-7 text-[color:var(--muted)]">
                  {t("schedule.description")}
                </p>
              </div>
              <div className="grid grid-cols-3 gap-2 rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.72)] p-3 text-center">
                <div>
                  <p className="text-2xl font-semibold">48</p>
                  <p className="text-xs text-[color:var(--muted)]">Teams</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold">12</p>
                  <p className="text-xs text-[color:var(--muted)]">Groups</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold">32</p>
                  <p className="text-xs text-[color:var(--muted)]">Knockout</p>
                </div>
              </div>
            </div>
            <p className="mt-6 text-xs text-[color:var(--muted)]">
              {t("schedule.mockGenerated", { time: data.generatedAt })}
            </p>
          </div>
        </section>
      )}

      <section className="mx-auto max-w-7xl space-y-10 px-4 pb-14 md:px-6">
        <GroupStageGrid
          groups={data.groups}
          qualificationRules={data.qualificationRules}
        />
        <KnockoutBracket rounds={data.rounds} bestThirdTeams={data.bestThirdTeams} />
      </section>
    </div>
  );
}
