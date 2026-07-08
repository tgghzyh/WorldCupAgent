/**
 * ChampionJourney Component (Presentation Layer)
 * Displays Champion Story Timeline
 * @TODO: Implement full UI in TP-2
 */

import type { ChampionPathViewModel } from "@/lib/tournament/types";

export interface ChampionJourneyProps {
  vm: ChampionPathViewModel;
}

export function ChampionJourney({ vm }: ChampionJourneyProps) {
  // TODO: Implement full UI in TP-2
  return (
    <div data-component="ChampionJourney" className="space-y-4">
      <div className="text-center mb-8">
        <h2 className="text-4xl font-bold text-gold">Champion Journey</h2>
        <p className="text-2xl text-text mt-2">{vm.champion}</p>
      </div>

      <div className="space-y-6">
        {vm.journeySteps.map((step) => (
          <div
            key={step.stage}
            data-stage={step.stage}
            className="bg-surface border-l-4 border-accent pl-4 py-3"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-3 h-3 rounded-full bg-${step.color}`} />
              <span className="text-sm font-semibold text-muted">{step.stageLabel}</span>
            </div>
            <p className="text-lg">{step.headline}</p>
            <p className="text-muted text-sm mt-1">{step.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
