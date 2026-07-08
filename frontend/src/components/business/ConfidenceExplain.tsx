/**
 * ConfidenceExplain Component (Business Layer)
 * Consumes ConfidenceExplainViewModel
 * @TODO: Implement full UI in TP-2
 */

import type { ConfidenceExplainViewModel } from "@/lib/tournament/types";

export interface ConfidenceExplainProps {
  vm: ConfidenceExplainViewModel;
}

export function ConfidenceExplain({ vm }: ConfidenceExplainProps) {
  // TODO: Implement full UI in TP-2
  return (
    <div data-component="ConfidenceExplain" data-level={vm.level}>
      <div className="bg-surface border-border rounded-lg p-4">
        <div className="text-3xl font-bold">{vm.score}</div>
        <p className="text-muted">{vm.level} Confidence</p>
        {/* TODO: Full implementation in TP-2 */}
      </div>
    </div>
  );
}
