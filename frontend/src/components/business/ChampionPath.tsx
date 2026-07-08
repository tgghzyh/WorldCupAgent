/**
 * ChampionPath Component (Business Layer)
 * Consumes ChampionPathViewModel
 * @TODO: Implement full UI in TP-2
 */

import type { ChampionPathViewModel } from "@/lib/tournament/types";

export interface ChampionPathProps {
  vm: ChampionPathViewModel;
}

export function ChampionPath({ vm }: ChampionPathProps) {
  // TODO: Implement full UI in TP-2
  return (
    <div data-component="ChampionPath" data-champion={vm.champion}>
      <div className="bg-surface border-border rounded-lg p-4">
        <h2 className="text-2xl font-bold">{vm.champion}</h2>
        <p className="text-muted">Probability: {(vm.probability * 100).toFixed(1)}%</p>
        {/* TODO: Full implementation in TP-2 */}
      </div>
    </div>
  );
}
