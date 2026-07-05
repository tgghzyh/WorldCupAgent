/**
 * BracketView Component (Business Layer)
 * Consumes BracketViewModel
 * @TODO: Implement full UI in TP-2
 */

import type { BracketViewModel } from "@/lib/tournament/types";

export interface BracketViewProps {
  vm: BracketViewModel;
}

export function BracketView({ vm }: BracketViewProps): JSX.Element {
  // TODO: Implement full UI in TP-2
  return (
    <div data-component="BracketView">
      <div className="bg-surface border-border rounded-lg p-4">
        <h2 className="text-xl font-bold">Tournament Bracket</h2>
        <p className="text-muted">Round of 16 to Final</p>
        {/* TODO: Full implementation in TP-2 */}
      </div>
    </div>
  );
}
