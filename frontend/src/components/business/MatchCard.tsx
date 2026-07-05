/**
 * MatchCard Component (Business Layer)
 * Consumes MatchCardViewModel
 * @TODO: Implement full UI in TP-2
 */

import type { MatchCardViewModel } from "@/lib/tournament/types";

export interface MatchCardProps {
  vm: MatchCardViewModel;
  onExpand?: () => void;
}

export function MatchCard({ vm, onExpand }: MatchCardProps): JSX.Element {
  // TODO: Implement full UI in TP-2
  return (
    <div data-component="MatchCard" data-match-id={vm.matchId}>
      <div className="bg-surface border-border rounded-lg p-4">
        <h3 className="text-lg font-semibold">{vm.title}</h3>
        <p className="text-muted">{vm.subtitle}</p>
        {/* TODO: Full implementation in TP-2 */}
      </div>
    </div>
  );
}
