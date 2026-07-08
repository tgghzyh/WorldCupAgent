import { AppChrome, PageIntro, ProbabilityBar } from "@/components/AppChrome";
import { loadSnapshotSync } from "@/lib/tournament/loader/snapshot.loader";

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function parseProbability(value: string): number {
  const parsed = Number.parseFloat(value.replace("%", ""));
  return Number.isNaN(parsed) ? 0 : parsed / 100;
}

export default function MatchPage() {
  const snapshot = loadSnapshotSync();
  const firstGroup = Object.values(snapshot.group_predictions)[0];
  const featuredMatch = firstGroup.matches[0];
  const homeWin = parseProbability(featuredMatch.home_win_prob);
  const draw = parseProbability(featuredMatch.draw_prob);
  const awayWin = parseProbability(featuredMatch.away_win_prob);
  const spread = Math.abs(homeWin - awayWin);
  const confidence = spread >= 0.3 ? "High" : spread >= 0.14 ? "Medium" : "Low";
  const favorite = homeWin >= awayWin ? featuredMatch.home_team : featuredMatch.away_team;

  return (
    <AppChrome>
      <PageIntro
        eyebrow="Match intelligence"
        title={`${featuredMatch.home_team} vs ${featuredMatch.away_team}`}
        description="A focused match report: probability, scoreline, factor attribution, and the plain-language reason behind the prediction."
      />

      <section className="mx-auto grid max-w-7xl gap-5 px-5 pb-16 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="glass-panel rounded-[2rem] p-8">
          <p className="text-sm text-muted">Predicted score</p>
          <p className="mt-4 text-7xl font-semibold">{featuredMatch.predicted_score}</p>
          <p className="mt-5 text-sm text-muted">Confidence: {confidence}</p>
          <div className="mt-8">
            <ProbabilityBar home={homeWin} draw={draw} away={awayWin} />
            <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
              <div>
                <p className="text-muted">Home win</p>
                <p className="mt-1 text-2xl font-semibold">{formatPercent(homeWin)}</p>
              </div>
              <div>
                <p className="text-muted">Draw</p>
                <p className="mt-1 text-2xl font-semibold">{formatPercent(draw)}</p>
              </div>
              <div>
                <p className="text-muted">Away win</p>
                <p className="mt-1 text-2xl font-semibold">{formatPercent(awayWin)}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="soft-card rounded-[2rem] p-8">
            <h2 className="text-2xl font-semibold">Why the model leans {favorite}</h2>
            <p className="mt-4 text-base leading-7 text-muted">{featuredMatch.reasoning}</p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              { label: "Home win", value: formatPercent(homeWin) },
              { label: "Draw", value: formatPercent(draw) },
              { label: "Away win", value: formatPercent(awayWin) },
            ].map((factor) => (
              <div key={factor.label} className="soft-card rounded-2xl p-5">
                <p className="text-sm text-muted">{factor.label}</p>
                <p className="mt-3 text-2xl font-semibold">{factor.value}</p>
              </div>
            ))}
          </div>
          <div className="soft-card rounded-[2rem] p-8">
            <h2 className="text-xl font-semibold">Confidence center</h2>
            <div className="mt-5 grid gap-3 text-sm text-muted md:grid-cols-3">
              <p>Snapshot: {snapshot.prediction_version}</p>
              <p>Stage: {featuredMatch.stage}</p>
              <p>Generated: {snapshot.snapshot_time}</p>
            </div>
          </div>
        </div>
      </section>
    </AppChrome>
  );
}
