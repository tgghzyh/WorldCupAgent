/**
 * GroupStageCard Component (Business Layer)
 * Displays group matches and standings
 * @TODO: Implement full UI in TP-2
 */

import type { GroupStageViewModel } from "@/lib/tournament/types";

export interface GroupStageCardProps {
  vm: GroupStageViewModel;
}

export function GroupStageCard({ vm }: GroupStageCardProps) {
  // TODO: Implement full UI in TP-2
  return (
    <div data-component="GroupStageCard" data-group={vm.group.letter}>
      <div className="bg-surface border-border rounded-lg p-4">
        <h3 className="text-lg font-bold">Group {vm.group.letter}</h3>
        <p className="text-muted">Qualifiers: {vm.group.qualifiers.join(", ")}</p>
        {/* TODO: Full implementation in TP-2 */}
      </div>
    </div>
  );
}
