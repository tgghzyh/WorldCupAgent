import { AppChrome, PageIntro, ProbabilityBar } from "@/components/AppChrome";
import { LocalizedText } from "@/components/LocalizedText";
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
        eyebrow={<LocalizedText en="Match intelligence" zh="比赛情报" />}
        title={<LocalizedText en={`${featuredMatch.home_team} vs ${featuredMatch.away_team}`} zh={`${featuredMatch.home_team} 对阵 ${featuredMatch.away_team}`} />}
        description={<LocalizedText en="A focused match report: probability, scoreline, factor attribution, and the plain-language reason behind the prediction." zh="单场比赛报告：胜平负概率、预测比分、因素归因，以及预测背后的通俗解释。" />}
      />

      <section className="mx-auto grid max-w-7xl gap-5 px-5 pb-16 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="glass-panel rounded-[2rem] p-8">
          <p className="text-sm text-muted"><LocalizedText en="Predicted score" zh="预测比分" /></p>
          <p className="mt-4 text-7xl font-semibold">{featuredMatch.predicted_score}</p>
          <p className="mt-5 text-sm text-muted"><LocalizedText en={`Confidence: ${confidence}`} zh={`置信度：${confidence === "High" ? "高" : confidence === "Medium" ? "中" : "低"}`} /></p>
          <div className="mt-8">
            <ProbabilityBar home={homeWin} draw={draw} away={awayWin} />
            <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
              <div>
                <p className="text-muted"><LocalizedText en="Home win" zh="主队获胜" /></p>
                <p className="mt-1 text-2xl font-semibold">{formatPercent(homeWin)}</p>
              </div>
              <div>
                <p className="text-muted"><LocalizedText en="Draw" zh="平局" /></p>
                <p className="mt-1 text-2xl font-semibold">{formatPercent(draw)}</p>
              </div>
              <div>
                <p className="text-muted"><LocalizedText en="Away win" zh="客队获胜" /></p>
                <p className="mt-1 text-2xl font-semibold">{formatPercent(awayWin)}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="soft-card rounded-[2rem] p-8">
            <h2 className="text-2xl font-semibold"><LocalizedText en={`Why the model leans ${favorite}`} zh={`模型为何倾向于 ${favorite}`} /></h2>
            <p className="mt-4 text-base leading-7 text-muted">{featuredMatch.reasoning}</p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              { id: "home", label: <LocalizedText en="Home win" zh="主队获胜" />, value: formatPercent(homeWin) },
              { id: "draw", label: <LocalizedText en="Draw" zh="平局" />, value: formatPercent(draw) },
              { id: "away", label: <LocalizedText en="Away win" zh="客队获胜" />, value: formatPercent(awayWin) },
            ].map((factor) => (
              <div key={factor.id} className="soft-card rounded-2xl p-5">
                <p className="text-sm text-muted">{factor.label}</p>
                <p className="mt-3 text-2xl font-semibold">{factor.value}</p>
              </div>
            ))}
          </div>
          <div className="soft-card rounded-[2rem] p-8">
            <h2 className="text-xl font-semibold"><LocalizedText en="Confidence center" zh="置信度信息" /></h2>
            <div className="mt-5 grid gap-3 text-sm text-muted md:grid-cols-3">
              <p><LocalizedText en={`Snapshot: ${snapshot.prediction_version}`} zh={`快照版本：${snapshot.prediction_version}`} /></p>
              <p><LocalizedText en={`Stage: ${featuredMatch.stage}`} zh="比赛阶段：小组赛" /></p>
              <p><LocalizedText en={`Generated: ${snapshot.snapshot_time}`} zh={`生成时间：${snapshot.snapshot_time}`} /></p>
            </div>
          </div>
        </div>
      </section>
    </AppChrome>
  );
}
