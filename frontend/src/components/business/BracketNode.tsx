/**
 * BracketNode Component (Business Layer)
 * Consumes BracketNodeViewModel
 * @TODO: Implement full UI in TP-2
 */

import type { BracketNodeViewModel } from "@/lib/tournament/types";

export interface BracketNodeProps {
  vm: BracketNodeViewModel;
  onExpand?: () => void;
}

export function BracketNode({ vm, onExpand }: BracketNodeProps): JSX.Element {
  // TODO: Implement full UI in TP-2
  return (
    <div
      data-component="BracketNode"
      data-node-id={vm.nodeId}
      data-stage={vm.stage}
      tabIndex={0}
      role="button"
      aria-label={`${vm.homeTeam} vs ${vm.awayTeam} - Press Enter to expand`}
      onKeyDown={(e) => {
        if (e.key === "Enter" && onExpand) {
          onExpand();
        }
      }}
      className="bg-surface border-border rounded-lg p-3 cursor-pointer hover:border-accent transition-colors"
    >
      <div className="flex justify-between">
        <span>{vm.homeTeam}</span>
        <span className="text-muted">{Math.round(vm.homeWinProb * 100)}%</span>
      </div>
      <div className="flex justify-between">
        <span>{vm.awayTeam}</span>
        <span className="text-muted">{Math.round(vm.awayWinProb * 100)}%</span>
      </div>
      {/* TODO: Full implementation in TP-2 */}
    </div>
  );
}
