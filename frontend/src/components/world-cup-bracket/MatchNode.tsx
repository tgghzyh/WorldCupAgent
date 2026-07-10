import { Activity, Clock, Lock, Trophy } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { CountryFlag } from "@/components/world-cup-bracket/CountryFlag";
import { LocalizedText } from "@/components/LocalizedText";
import { useI18n } from "@/i18n";
import { cn } from "@/lib/utils";
import type { BracketMatch, BracketTeamSlot } from "@/lib/world-cup-bracket/types";

type MatchNodeProps = {
  match: BracketMatch;
  compact?: boolean;
  onSelect?: (match: BracketMatch) => void;
};

function TeamRow({
  slot,
  isWinner,
  muted,
}: {
  slot: BracketTeamSlot;
  isWinner: boolean;
  muted: boolean;
}) {
  return (
    <div
      className={cn(
        "grid grid-cols-[1.25rem_1fr_3rem_2.5rem] items-center gap-2 rounded-md px-2 py-1.5",
        isWinner && "bg-[rgba(4,120,87,0.10)] text-[color:var(--green)]"
      )}
    >
      <CountryFlag team={slot.team} className={cn(muted && "grayscale")} />
      <span className="min-w-0 truncate text-sm font-medium">{slot.team.name}</span>
      <span className="text-right text-xs tabular-nums text-[color:var(--muted)]">
        {Math.round(slot.probability * 100)}%
      </span>
      <span className="text-right font-mono text-sm font-semibold">
        {slot.score ?? "-"}
      </span>
    </div>
  );
}

export function MatchNode({ match, compact = false, onSelect }: MatchNodeProps) {
  const { t } = useI18n();
  const isCompleted = match.status === "completed";
  const isLive = match.status === "live";
  const score = match.actualScore ?? match.predictedScore ?? t("schedule.tbd");

  return (
    <article
      className={cn(
        "relative w-[250px] rounded-lg border bg-[rgba(255,251,244,0.94)] p-3 shadow-[0_10px_28px_rgba(79,58,34,0.08)]",
        isCompleted && "border-[rgba(117,107,94,0.28)] opacity-60 grayscale",
        isLive && "border-[color:var(--brand-red)] shadow-[0_0_0_4px_rgba(197,48,48,0.08)]",
        !isCompleted && !isLive && "border-[color:var(--border)]",
        compact && "w-[230px]"
      )}
    >
      <button
        type="button"
        data-pan-ignore="true"
        data-testid={`match-node-${match.id}`}
        aria-label={`${match.home.team.name} ${t("drawer.vs")} ${match.away.team.name}`}
        className="absolute inset-0 z-10 cursor-pointer rounded-lg focus-visible:ring-2 focus-visible:ring-[color:var(--brand-blue)]"
        onClick={() => onSelect?.(match)}
      />
      {isLive && (
        <span className="absolute -right-1 -top-1 h-3 w-3 animate-ping rounded-full bg-[color:var(--brand-red)]" />
      )}
      <div className="mb-2 flex items-center justify-between gap-3">
        <Badge
          className={cn(
            "gap-1 border-transparent",
            isCompleted && "bg-[rgba(117,107,94,0.12)]",
            isLive && "bg-[rgba(197,48,48,0.10)] text-[color:var(--brand-red)]",
            match.status === "upcoming" && "bg-[rgba(10,102,194,0.10)] text-[color:var(--brand-blue)]"
          )}
        >
          {isCompleted ? <Lock className="h-3 w-3" /> : isLive ? <Activity className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
          {match.kickoffLabel}
        </Badge>
        <span className="truncate text-xs text-[color:var(--muted)]">{match.label}</span>
      </div>

      <div className="space-y-1">
        <TeamRow
          slot={match.home}
          isWinner={match.winnerTeamId === match.home.team.id}
          muted={isCompleted}
        />
        <TeamRow
          slot={match.away}
          isWinner={match.winnerTeamId === match.away.team.id}
          muted={isCompleted}
        />
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-[rgba(226,212,193,0.7)] pt-2">
        <span className="text-xs text-[color:var(--muted)]">
          {match.actualScore ? <LocalizedText en="Actual score" zh="实际比分" /> : <LocalizedText en="Predicted score" zh="预测比分" />}
        </span>
        <span className="flex items-center gap-1 font-mono text-sm font-semibold text-[color:var(--text)]">
          {match.stage === "final" && <Trophy className="h-3.5 w-3.5 text-[color:var(--gold)]" />}
          {score}
        </span>
      </div>
    </article>
  );
}
