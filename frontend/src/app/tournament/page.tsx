import { AppChrome, PageIntro } from "@/components/AppChrome";
import { LocalizedStage, LocalizedText } from "@/components/LocalizedText";
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
  return "";
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
        eyebrow={<LocalizedText en="Tournament path" zh="冠军晋级路径" />}
        title={<LocalizedText en={`${champion}'s route to the trophy`} zh={`${champion}的夺冠路径`} />}
        description={<LocalizedText en="The bracket page turns the prediction into a story: which rounds matter, where uncertainty spikes, and how the champion survives the path." zh="赛程树把预测转化为清晰的晋级故事：哪些轮次最关键、不确定性出现在哪里，以及冠军如何走到最后。" />}
      />

      <section className="mx-auto grid max-w-7xl gap-5 px-5 pb-16 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="glass-panel rounded-[2rem] p-8">
          <p className="text-sm text-muted"><LocalizedText en="Projected champion" zh="预测冠军" /></p>
          <p className="mt-3 text-5xl font-semibold">{champion}</p>
          <p className="mt-3 text-2xl text-gold">{formatPercent(snapshot.champion_probability)}</p>
          <div className="mt-8 space-y-4">
            {tournamentPath.map((step) => (
              <div key={step.stage} className="rounded-2xl border hairline bg-surface/70 p-4">
                <div className="flex items-center justify-between gap-4">
                  <p className="font-medium"><LocalizedStage stage={step.stage} /></p>
                  <p className="text-sm text-muted">{formatPercent(step.probability)}</p>
                </div>
                <p className="mt-2 text-sm text-muted">
                  <LocalizedText en={`vs ${step.opponent} · ${step.note}`} zh={`对阵 ${step.opponent} · ${step.note}`} />
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="soft-card overflow-x-auto rounded-[2rem] p-6">
          <div className="grid min-w-[1100px] grid-cols-5 gap-4">
            {bracketData.rounds.map((round) => (
              <div key={round.title}>
                <p className="mb-4 text-center text-sm font-medium text-muted"><LocalizedStage stage={round.title} /></p>
                <div className="space-y-4">
                  {round.matches.map((match) => (
                    <div key={match.id} className="rounded-2xl border hairline bg-surface/80 p-4 text-sm font-medium">
                      <div>
                        <LocalizedText
                          en={`${match.home.team.name} vs ${match.away.team.name}`}
                          zh={`${match.home.team.name} 对阵 ${match.away.team.name}`}
                        />
                      </div>
                      <div className="mt-2 text-xs text-muted">
                        <LocalizedText en={`${match.predictedScore} / winner: ${winnerNameFor(match)}`} zh={`${match.predictedScore} / 胜者：${winnerNameFor(match)}`} />
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
