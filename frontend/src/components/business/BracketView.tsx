import { KnockoutBracket } from "@/components/world-cup-bracket/KnockoutBracket";
import type { BracketRound, GroupStanding } from "@/lib/world-cup-bracket/types";
import type { BracketViewModel } from "@/lib/tournament/types";

export function BracketView({
  rounds,
  bestThirdTeams,
  vm,
}: {
  rounds?: BracketRound[];
  bestThirdTeams?: GroupStanding[];
  vm?: BracketViewModel;
}) {
  if (rounds && bestThirdTeams) {
    return <KnockoutBracket rounds={rounds} bestThirdTeams={bestThirdTeams} />;
  }

  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-5 text-sm text-[color:var(--muted)]">
      Legacy bracket view model detected
      {vm ? ` (${vm.roundOf16.length} round-of-16 nodes).` : "."} Use the
      new props-driven World Cup bracket data shape for the interactive 32-team
      tree.
    </div>
  );
}
