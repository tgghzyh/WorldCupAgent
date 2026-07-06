"use client";

import { useI18n } from "@/i18n";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { TeamInfoCard, MatchCardBilingual } from "@/components/TeamComponents";
import { PlayerCard, TeamPlayers } from "@/components/PlayerComponents";
import { getTeamById, getTopTeams, getTopPlayers, getTeamComparison } from "@/knowledge";

/**
 * Demo Page - i18n and Knowledge Layer Showcase
 * This page demonstrates the bilingual support and football knowledge layer
 */
export default function DemoPage(): JSX.Element {
  const { locale, t } = useI18n();

  const topTeams = getTopTeams(6);
  const topPlayers = getTopPlayers(5);

  // Sample match data
  const sampleMatch = {
    homeTeamId: "argentina",
    awayTeamId: "brazil",
    homeWinProb: 0.52,
    drawProb: 0.22,
    awayWinProb: 0.26,
    kickoffTime: "2026-07-15T21:00:00Z",
    confidence: "high" as const,
  };

  return (
    <main className="min-h-screen bg-[#0a0e14]">
      {/* Header with Language Switcher */}
      <header className="border-b border-[#1e2a3a] bg-[#131a24]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">⚽</span>
            <div>
              <h1 className="text-xl font-bold text-[#cdd9e5]">
                {locale === "zh" ? "足球知识系统" : "Football Knowledge System"}
              </h1>
              <p className="text-xs text-[#768390]">
                {locale === "zh" ? "双语世界杯知识层演示" : "Bilingual WC2026 Knowledge Layer Demo"}
              </p>
            </div>
          </div>
          <LanguageSwitcher />
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-8 space-y-12">
        {/* Section 1: Translation Demo */}
        <section>
          <h2 className="text-2xl font-bold text-[#cdd9e5] mb-6 flex items-center gap-2">
            <span className="text-[#58a6ff]">🌐</span>
            {t("common.home")} - {t("footer.powered_by")} i18n
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <DemoCard 
              title={t("prediction.home_win")} 
              value="79.8%"
              color="#3fb950"
            />
            <DemoCard 
              title={t("prediction.draw")} 
              value="6.7%"
              color="#d29922"
            />
            <DemoCard 
              title={t("prediction.away_win")} 
              value="13.6%"
              color="#f85149"
            />
            <DemoCard 
              title={t("confidence.high")} 
              value="87"
              color="#58a6ff"
            />
          </div>
        </section>

        {/* Section 2: Featured Match Card */}
        <section>
          <h2 className="text-2xl font-bold text-[#cdd9e5] mb-6 flex items-center gap-2">
            <span className="text-[#3fb950]">⚽</span>
            {locale === "zh" ? "比赛卡片组件" : "Match Card Component"}
          </h2>
          
          <MatchCardBilingual
            homeTeamId={sampleMatch.homeTeamId}
            awayTeamId={sampleMatch.awayTeamId}
            homeWinProb={sampleMatch.homeWinProb}
            drawProb={sampleMatch.drawProb}
            awayWinProb={sampleMatch.awayWinProb}
            kickoffTime={sampleMatch.kickoffTime}
            confidence={sampleMatch.confidence}
          />
        </section>

        {/* Section 3: Top Teams */}
        <section>
          <h2 className="text-2xl font-bold text-[#cdd9e5] mb-6 flex items-center gap-2">
            <span className="text-[#ffd700]">🏆</span>
            {locale === "zh" ? "夺冠热门" : "Championship Favorites"}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {topTeams.map((team, index) => (
              <TeamInfoCard key={team.id} teamId={team.id} showDetails={true} />
            ))}
          </div>
        </section>

        {/* Section 4: Team Players */}
        <section>
          <h2 className="text-2xl font-bold text-[#cdd9e5] mb-6 flex items-center gap-2">
            <span className="text-[#bc8cff]">⭐</span>
            {locale === "zh" ? "明星球员" : "Star Players"}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {topPlayers.slice(0, 3).map((player) => (
              <PlayerCard key={player.id} playerId={player.id} />
            ))}
          </div>
        </section>

        {/* Section 5: Team with Relations */}
        <section>
          <h2 className="text-2xl font-bold text-[#cdd9e5] mb-6 flex items-center gap-2">
            <span className="text-[#e8854a]">📊</span>
            {locale === "zh" ? "阿根廷队完整信息" : "Argentina - Full Team Info"}
          </h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TeamInfoCard teamId="argentina" showDetails={true} />
            <TeamPlayers teamId="argentina" maxPlayers={3} />
          </div>
        </section>

        {/* Section 6: Translation Examples */}
        <section>
          <h2 className="text-2xl font-bold text-[#cdd9e5] mb-6 flex items-center gap-2">
            <span className="text-[#58a6ff]">🔤</span>
            {locale === "zh" ? "翻译示例" : "Translation Examples"}
          </h2>
          
          <div className="bg-[#131a24] border border-[#1e2a3a] rounded-xl p-6">
            <table className="w-full">
              <thead>
                <tr className="text-left border-b border-[#1e2a3a]">
                  <th className="pb-3 text-[#768390] text-sm">
                    {locale === "zh" ? "键" : "Key"}
                  </th>
                  <th className="pb-3 text-[#768390] text-sm">
                    {locale === "zh" ? "中文" : "Chinese"}
                  </th>
                  <th className="pb-3 text-[#768390] text-sm">
                    {locale === "zh" ? "英文" : "English"}
                  </th>
                </tr>
              </thead>
              <tbody className="text-sm space-y-2">
                <tr>
                  <td className="py-2 text-[#58a6ff] font-mono">stages.final</td>
                  <td className="py-2 text-[#cdd9e5]">{t("stages.final")}</td>
                  <td className="py-2 text-[#768390]">Final</td>
                </tr>
                <tr>
                  <td className="py-2 text-[#58a6ff] font-mono">confidence.high</td>
                  <td className="py-2 text-[#cdd9e5]">{t("confidence.high")}</td>
                  <td className="py-2 text-[#768390]">High</td>
                </tr>
                <tr>
                  <td className="py-2 text-[#58a6ff] font-mono">prediction.model</td>
                  <td className="py-2 text-[#cdd9e5]">{t("prediction.model")}</td>
                  <td className="py-2 text-[#768390]">Prediction Model</td>
                </tr>
                <tr>
                  <td className="py-2 text-[#58a6ff] font-mono">agent.workflow</td>
                  <td className="py-2 text-[#cdd9e5]">{t("agent.workflow")}</td>
                  <td className="py-2 text-[#768390]">Agent Workflow</td>
                </tr>
                <tr>
                  <td className="py-2 text-[#58a6ff] font-mono">teams.argentina</td>
                  <td className="py-2 text-[#cdd9e5]">{t("teams.argentina")}</td>
                  <td className="py-2 text-[#768390]">Argentina</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 7: Knowledge Layer Stats */}
        <section>
          <h2 className="text-2xl font-bold text-[#cdd9e5] mb-6 flex items-center gap-2">
            <span className="text-[#3fb950]">📈</span>
            {locale === "zh" ? "知识层统计" : "Knowledge Layer Stats"}
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard 
              label={locale === "zh" ? "球队数量" : "Teams"}
              value="48"
              icon="🏳️"
            />
            <StatCard 
              label={locale === "zh" ? "球员数量" : "Players"}
              value="60+"
              icon="⚽"
            />
            <StatCard 
              label={locale === "zh" ? "教练数量" : "Coaches"}
              value="48"
              icon="👔"
            />
            <StatCard 
              label={locale === "zh" ? "支持语言" : "Languages"}
              value="2"
              icon="🌐"
            />
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center py-8 border-t border-[#1e2a3a]">
          <p className="text-[#768390] text-sm">
            {locale === "zh" 
              ? "WC2026 AI Prediction Agent - 足球知识层演示" 
              : "WC2026 AI Prediction Agent - Football Knowledge Layer Demo"}
          </p>
          <p className="text-[#768390]/60 text-xs mt-2">
            {locale === "zh"
              ? "由 Cursor AI 提供技术支持"
              : "Powered by Cursor AI"}
          </p>
        </footer>
      </div>
    </main>
  );
}

// Demo helper components
function DemoCard({ title, value, color }: { title: string; value: string; color: string }) {
  return (
    <div className="bg-[#131a24] border border-[#1e2a3a] rounded-lg p-4 text-center">
      <p className="text-sm text-[#768390] mb-1">{title}</p>
      <p className="text-2xl font-bold" style={{ color }}>
        {value}
      </p>
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="bg-[#131a24] border border-[#1e2a3a] rounded-lg p-6 text-center">
      <span className="text-3xl">{icon}</span>
      <p className="text-3xl font-bold text-[#58a6ff] mt-2">{value}</p>
      <p className="text-sm text-[#768390]">{label}</p>
    </div>
  );
}
