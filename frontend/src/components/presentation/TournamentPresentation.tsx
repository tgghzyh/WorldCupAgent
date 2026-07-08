/**
 * TournamentPresentation Component (Presentation Layer)
 * Main container for Tournament page
 * Combines business components
 * @TODO: Implement full UI in TP-2
 */

import { BracketView } from "@/components/business/BracketView";
import { ChampionPath } from "@/components/business/ChampionPath";
import type { BracketViewModel, ChampionPathViewModel } from "@/lib/tournament/types";

export interface TournamentPresentationProps {
  bracketVm: BracketViewModel;
  championPathVm: ChampionPathViewModel;
}

export function TournamentPresentation({
  bracketVm,
  championPathVm,
}: TournamentPresentationProps) {
  // TODO: Implement full layout in TP-2
  return (
    <div data-component="TournamentPresentation" className="min-h-screen bg-bg p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-text">World Cup 2026 AI Prediction</h1>
        <p className="text-muted">Tournament Overview</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <section>
          <ChampionPath vm={championPathVm} />
        </section>
        <section>
          <BracketView vm={bracketVm} />
        </section>
      </div>
    </div>
  );
}
