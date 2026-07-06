"use client";

import { useI18n } from "@/i18n";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { TeamInfoCard, MatchCardBilingual } from "@/components/TeamComponents";
import { PlayerCard, TeamPlayers } from "@/components/PlayerComponents";
import { getTopTeams, getTopPlayers } from "@/knowledge";

/**
 * Demo Page - Redesigned Layout
 */
export default function DemoPage(): JSX.Element {
  const { locale, t } = useI18n();

  const topTeams = getTopTeams(6);
  const topPlayers = getTopPlayers(5);

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
    <div className="min-h-screen bg-gradient-to-br from-[#0f1419] via-[#1a1f2e] to-[#0d1117]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#0d1117]/90 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#ff6b6b] to-[#ffa502] flex items-center justify-center shadow-lg shadow-orange-500/20">
              <span className="text-2xl">⚽</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">
                {locale === "zh" ? "足球知识系统" : "Football Knowledge"}
              </h1>
              <p className="text-xs text-white/40">
                {locale === "zh" ? "WC2026 双语智能知识层" : "WC2026 Bilingual AI Knowledge"}
              </p>
            </div>
          </div>
          <LanguageSwitcher />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-10 space-y-12">
        {/* Hero Section */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-[#1e3a5f] via-[#2d1b4e] to-[#1a2a3a] p-10">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSA2MCAwIEwgMCAwIDAgNjAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-50" />
          <div className="relative flex flex-col lg:flex-row items-center justify-between gap-8">
            <div className="text-center lg:text-left">
              <h2 className="text-4xl lg:text-5xl font-bold text-white mb-4">
                {locale === "zh" ? "世界杯智能预测" : "World Cup Predictions"}
              </h2>
              <p className="text-white/60 text-lg max-w-xl">
                {locale === "zh"
                  ? "基于 AI Agent 的世界杯比赛预测系统，整合全球 48 支球队数据"
                  : "AI-powered World Cup predictions with 48 global teams data"}
              </p>
            </div>
            <div className="flex gap-6">
              <div className="text-center">
                <div className="text-4xl font-bold text-[#ffa502]">48</div>
                <div className="text-white/40 text-sm">{locale === "zh" ? "球队" : "Teams"}</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-[#ff6b6b]">60+</div>
                <div className="text-white/40 text-sm">{locale === "zh" ? "球员" : "Players"}</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-[#a855f7]">2</div>
                <div className="text-white/40 text-sm">{locale === "zh" ? "语言" : "Languages"}</div>
              </div>
            </div>
          </div>
        </section>

        {/* Featured Match */}
        <section>
          <SectionHeader
            icon="🔥"
            iconBg="from-[#ff6b6b] to-[#ff4757]"
            title={locale === "zh" ? "焦点对决" : "Featured Match"}
          />
          <div className="flex justify-center">
            <MatchCardBilingual
              homeTeamId={sampleMatch.homeTeamId}
              awayTeamId={sampleMatch.awayTeamId}
              homeWinProb={sampleMatch.homeWinProb}
              drawProb={sampleMatch.drawProb}
              awayWinProb={sampleMatch.awayWinProb}
              kickoffTime={sampleMatch.kickoffTime}
              confidence={sampleMatch.confidence}
            />
          </div>
        </section>

        {/* Top Teams */}
        <section>
          <SectionHeader
            icon="🏆"
            iconBg="from-[#ffd700] to-[#ffa502]"
            title={locale === "zh" ? "夺冠热门 TOP 6" : "Championship Favorites"}
            subtitle={locale === "zh" ? "综合实力最强的六支球队" : "Top 6 teams by overall strength"}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topTeams.map((team) => (
              <div key={team.id} className="group">
                <TeamInfoCard teamId={team.id} showDetails={true} />
              </div>
            ))}
          </div>
        </section>

        {/* Star Players */}
        <section>
          <SectionHeader
            icon="⭐"
            iconBg="from-[#a855f7] to-[#6366f1]"
            title={locale === "zh" ? "明星球员" : "Star Players"}
            subtitle={locale === "zh" ? "各队核心球员实力分析" : "Key player analysis"}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topPlayers.slice(0, 3).map((player) => (
              <PlayerCard key={player.id} playerId={player.id} />
            ))}
          </div>
        </section>

        {/* Argentina Deep Dive */}
        <section>
          <SectionHeader
            icon="🇦🇷"
            iconBg="from-[#75aadb] to-[#75aadb]"
            title={locale === "zh" ? "深度解析：阿根廷" : "Deep Dive: Argentina"}
            subtitle={locale === "zh" ? "2022冠军能否卫冕？" : "Can the 2022 champions defend their title?"}
          />
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-2">
              <TeamInfoCard teamId="argentina" showDetails={true} />
            </div>
            <div className="lg:col-span-3">
              <TeamPlayers teamId="argentina" maxPlayers={5} />
            </div>
          </div>
        </section>

        {/* Translation Showcase */}
        <section>
          <SectionHeader
            icon="🌐"
            iconBg="from-[#22c55e] to-[#10b981]"
            title={locale === "zh" ? "双语支持展示" : "Bilingual Support"}
            subtitle={locale === "zh" ? "一键切换中英文" : "Switch languages with one click"}
          />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <TranslationCard
              category={locale === "zh" ? "比赛阶段" : "Match Stages"}
              items={[
                { key: "stages.final", label: t("stages.final") },
                { key: "stages.semifinal", label: t("stages.semifinal") },
                { key: "stages.quarterfinal", label: t("stages.quarterfinal") },
                { key: "stages.group", label: t("stages.group") },
              ]}
            />
            <TranslationCard
              category={locale === "zh" ? "预测相关" : "Predictions"}
              items={[
                { key: "prediction.home_win", label: t("prediction.home_win") },
                { key: "prediction.away_win", label: t("prediction.away_win") },
                { key: "prediction.draw", label: t("prediction.draw") },
                { key: "prediction.model", label: t("prediction.model") },
              ]}
            />
            <TranslationCard
              category={locale === "zh" ? "置信度" : "Confidence"}
              items={[
                { key: "confidence.high", label: t("confidence.high") },
                { key: "confidence.medium", label: t("confidence.medium") },
                { key: "confidence.low", label: t("confidence.low") },
                { key: "agent.workflow", label: t("agent.workflow") },
              ]}
            />
          </div>
        </section>

        {/* Features Grid */}
        <section>
          <SectionHeader
            icon="✨"
            iconBg="from-[#3b82f6] to-[#6366f1]"
            title={locale === "zh" ? "系统特性" : "Features"}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <FeatureCard
              icon="🤖"
              title={locale === "zh" ? "AI 智能预测" : "AI Predictions"}
              desc={locale === "zh" ? "基于多源数据的深度学习模型" : "Deep learning from multiple data sources"}
            />
            <FeatureCard
              icon="🌐"
              title={locale === "zh" ? "双语界面" : "Bilingual UI"}
              desc={locale === "zh" ? "中英文无缝切换体验" : "Seamless EN/ZH switching"}
            />
            <FeatureCard
              icon="📊"
              title={locale === "zh" ? "实时数据" : "Real-time Data"}
              desc={locale === "zh" ? "FIFA排名、赔率等综合分析" : "FIFA rankings, odds analysis"}
            />
            <FeatureCard
              icon="🔄"
              title={locale === "zh" ? "持续更新" : "Live Updates"}
              desc={locale === "zh" ? "跟随赛事进程动态调整" : "Dynamic updates with tournament progress"}
            />
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-16 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-white/40 text-sm">
            WC2026 AI Prediction Agent
          </p>
          <p className="text-white/20 text-xs mt-2">
            {locale === "zh" ? "由 Cursor AI 提供技术支持" : "Powered by Cursor AI"}
          </p>
        </div>
      </footer>
    </div>
  );
}

function SectionHeader({
  icon,
  iconBg,
  title,
  subtitle,
}: {
  icon: string;
  iconBg: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="flex items-center gap-4 mb-6">
      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${iconBg} flex items-center justify-center text-2xl shadow-lg`}>
        {icon}
      </div>
      <div>
        <h2 className="text-2xl font-bold text-white">{title}</h2>
        {subtitle && <p className="text-white/40 text-sm">{subtitle}</p>}
      </div>
    </div>
  );
}

function TranslationCard({
  category,
  items,
}: {
  category: string;
  items: { key: string; label: string }[];
}) {
  return (
    <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden">
      <div className="px-5 py-4 bg-white/5 border-b border-white/5">
        <h3 className="text-white font-semibold">{category}</h3>
      </div>
      <div className="p-5 space-y-3">
        {items.map((item) => (
          <div key={item.key} className="flex items-center justify-between">
            <code className="text-[#58a6ff] text-xs bg-[#58a6ff]/10 px-2 py-1 rounded">
              {item.key}
            </code>
            <span className="text-white/80 text-sm">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:bg-white/10 transition-colors">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="text-white font-semibold mb-1">{title}</h3>
      <p className="text-white/40 text-sm">{desc}</p>
    </div>
  );
}
