import { AppChrome, PageIntro } from "@/components/AppChrome";
import { loadSnapshotSync } from "@/lib/tournament/loader/snapshot.loader";
import type { BracketMatch } from "@/lib/world-cup-bracket/types";
import { snapshotToWorldCupBracketData } from "@/lib/world-cup-bracket/snapshot-to-bracket";

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function winProbabilityFor(match: BracketMatch, team: string): number {
  if (match.home.team.name === team) return match.home.probability;
  if (match.away.team.name === team) return match.away.probability;
  return Math.max(match.home.probability, match.away.probability);
}

function opponentFor(match: BracketMatch, team: string): string {
  if (match.home.team.name === team) return match.away.team.name;
  if (match.away.team.name === team) return match.home.team.name;
  return `${match.home.team.name} / ${match.away.team.name}`;
}

function winnerNameFor(match: BracketMatch): string {
  if (match.winnerTeamId === match.home.team.id) return match.home.team.name;
  if (match.winnerTeamId === match.away.team.id) return match.away.team.name;
  return "Projected";
}

export default function TournamentPage() {
  const snapshot = loadSnapshotSync();
  const bracketData = snapshotToWorldCupBracketData(snapshot);
  const champion = snapshot.champion;
  const tournamentPath = bracketData.rounds
    .map((round) => {
      const match =
        round.matches.find((item) => item.home.team.name === champion || item.away.team.name === champion) ??
        round.matches.find((item) => item.winnerTeamId === champion.toLowerCase()) ??
        round.matches[0];

      return {
        stage: round.title,
        opponent: opponentFor(match, champion),
        probability: winProbabilityFor(match, champion),
        note: match.detail.reasoningFactors[0]?.description ?? match.advancementRule,
      };
    })
    .filter(Boolean);

  return (
    <AppChrome>
      <PageIntro
        eyebrow="Tournament path"
        title={`${champion}'s route to the trophy`}
        description="The bracket page turns the prediction into a story: which rounds matter, where uncertainty spikes, and how the champion survives the path."
      />

      <section className="mx-auto grid max-w-7xl gap-5 px-5 pb-16 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="glass-panel rounded-[2rem] p-8">
          <p className="text-sm text-muted">Projected champion</p>
          <p className="mt-3 text-5xl font-semibold">{champion}</p>
          <p className="mt-3 text-2xl text-gold">{formatPercent(snapshot.champion_probability)}</p>
          <div className="mt-8 space-y-4">
            {tournamentPath.map((step) => (
              <div key={step.stage} className="rounded-2xl border hairline bg-surface/70 p-4">
                <div className="flex items-center justify-between gap-4">
                  <p className="font-medium">{step.stage}</p>
                  <p className="text-sm text-muted">{formatPercent(step.probability)}</p>
                </div>
                <p className="mt-2 text-sm text-muted">
                  vs {step.opponent} · {step.note}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="soft-card overflow-x-auto rounded-[2rem] p-6">
          <div className="grid min-w-[1100px] grid-cols-5 gap-4">
            {bracketData.rounds.map((round) => (
              <div key={round.title}>
                <p className="mb-4 text-center text-sm font-medium text-muted">{round.title}</p>
                <div className="space-y-4">
                  {round.matches.map((match) => (
                    <div key={match.id} className="rounded-2xl border hairline bg-surface/80 p-4 text-sm font-medium">
                      <div>{match.home.team.name} vs {match.away.team.name}</div>
                      <div className="mt-2 text-xs text-muted">
                        {match.predictedScore} / winner: {winnerNameFor(match)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </AppChrome>
  );
}
