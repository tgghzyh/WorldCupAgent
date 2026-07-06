"use client";

import { useI18n } from "@/i18n";
import { getTeamById, getTeamFlag, getTeamName } from "@/knowledge";
import { Locale } from "@/i18n";

interface TeamBadgeProps {
  teamId: string;
  showFlag?: boolean;
  size?: "sm" | "md" | "lg";
}

export function TeamBadge({ teamId, showFlag = true, size = "md" }: TeamBadgeProps) {
  const { locale } = useI18n();
  const team = getTeamById(teamId);
  
  if (!team) {
    return (
      <div className="flex items-center gap-2">
        {showFlag && <span className="text-lg">🏳️</span>}
        <span className="text-[#768390]">{teamId}</span>
      </div>
    );
  }

  const name = locale === "zh" ? team.names.zh : team.names.en;
  const sizeClasses = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg",
  };

  return (
    <div className="flex items-center gap-2">
      {showFlag && <span className="text-xl">{team.flag_emoji}</span>}
      <span className={`font-medium text-[#cdd9e5] ${sizeClasses[size]}`}>{name}</span>
    </div>
  );
}

interface MatchCardBilingualProps {
  homeTeamId: string;
  awayTeamId: string;
  homeWinProb: number;
  drawProb: number;
  awayWinProb: number;
  kickoffTime?: string;
  group?: string;
  confidence?: "high" | "medium" | "low";
  onClick?: () => void;
}

export function MatchCardBilingual({
  homeTeamId,
  awayTeamId,
  homeWinProb,
  drawProb,
  awayWinProb,
  kickoffTime,
  group,
  confidence,
  onClick,
}: MatchCardBilingualProps) {
  const { locale, t } = useI18n();
  const homeTeam = getTeamById(homeTeamId);
  const awayTeam = getTeamById(awayTeamId);

  const homeName = homeTeam
    ? locale === "zh"
      ? homeTeam.names.zh
      : homeTeam.names.en
    : homeTeamId;
  const awayName = awayTeam
    ? locale === "zh"
      ? awayTeam.names.zh
      : awayTeam.names.en
    : awayTeamId;

  const confidenceColors = {
    high: "bg-[#3fb950]/20 text-[#3fb950]",
    medium: "bg-[#d29922]/20 text-[#d29922]",
    low: "bg-[#f85149]/20 text-[#f85149]",
  };

  const confidenceLabels = {
    high: t("confidence.high"),
    medium: t("confidence.medium"),
    low: t("confidence.low"),
  };

  return (
    <div
      className="bg-[#131a24] border border-[#1e2a3a] rounded-xl p-4 hover:border-[#58a6ff]/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        {group && (
          <span className="text-xs text-[#768390] bg-[#1a2333] px-2 py-1 rounded">
            {t("stages.group").replace("{g}", group)}
          </span>
        )}
        {confidence && (
          <span
            className={`text-xs px-2 py-1 rounded ${confidenceColors[confidence]}`}
          >
            {confidenceLabels[confidence]}
          </span>
        )}
      </div>

      {/* Teams */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{homeTeam?.flag_emoji || "🏳️"}</span>
          <span className="font-semibold text-[#cdd9e5]">{homeName}</span>
        </div>
        <span className="text-[#768390] text-sm">vs</span>
        <div className="flex items-center gap-2">
          <span className="font-semibold text-[#cdd9e5]">{awayName}</span>
          <span className="text-2xl">{awayTeam?.flag_emoji || "🏳️"}</span>
        </div>
      </div>

      {/* Probability Bar */}
      <div className="mb-4">
        <div className="flex h-3 rounded-full overflow-hidden bg-[#1a2333]">
          <div
            className="bg-[#3fb950] transition-all"
            style={{ width: `${homeWinProb * 100}%` }}
          />
          <div
            className="bg-[#d29922] transition-all"
            style={{ width: `${drawProb * 100}%` }}
          />
          <div
            className="bg-[#f85149] transition-all"
            style={{ width: `${awayWinProb * 100}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span className="text-[#3fb950]">
            {Math.round(homeWinProb * 100)}% {t("prediction.home_win")}
          </span>
          <span className="text-[#d29922]">
            {Math.round(drawProb * 100)}% {t("prediction.draw")}
          </span>
          <span className="text-[#f85149]">
            {Math.round(awayWinProb * 100)}% {t("prediction.away_win")}
          </span>
        </div>
      </div>

      {/* Footer */}
      {kickoffTime && (
        <div className="flex items-center justify-between text-xs text-[#768390]">
          <span>{t("match.kickoff")}</span>
          <span>{new Date(kickoffTime).toLocaleString(locale === "zh" ? "zh-CN" : "en-US")}</span>
        </div>
      )}
    </div>
  );
}

interface TeamInfoCardProps {
  teamId: string;
  showDetails?: boolean;
}

export function TeamInfoCard({ teamId, showDetails = false }: TeamInfoCardProps) {
  const { locale, t } = useI18n();
  const team = getTeamById(teamId);

  if (!team) {
    return (
      <div className="bg-[#131a24] border border-[#1e2a3a] rounded-xl p-4">
        <span className="text-[#768390]">Team not found: {teamId}</span>
      </div>
    );
  }

  const name = locale === "zh" ? team.names.zh : team.names.en;
  const nickname = locale === "zh" ? team.nickname.zh : team.nickname.en;
  const history = locale === "zh" ? team.tournament_history.zh : team.tournament_history.en;
  const style = locale === "zh" ? team.tactical_info.style_zh : team.tactical_info.style_en;
  const strengths = locale === "zh"
    ? team.tactical_info.key_strengths_zh
    : team.tactical_info.key_strengths_en;

  return (
    <div className="bg-[#131a24] border border-[#1e2a3a] rounded-xl overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#1a2333] to-[#131a24] p-4">
        <div className="flex items-center gap-3">
          <span className="text-4xl">{team.flag_emoji}</span>
          <div>
            <h3 className="text-xl font-bold text-[#cdd9e5]">{name}</h3>
            <p className="text-sm text-[#768390]">
              {locale === "zh" ? "绰号" : "Nickname"}: {nickname}
            </p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="p-4 grid grid-cols-3 gap-4 border-b border-[#1e2a3a]">
        <div className="text-center">
          <p className="text-2xl font-bold text-[#58a6ff]">{team.worldcup_titles}</p>
          <p className="text-xs text-[#768390]">
            {locale === "zh" ? "冠军次数" : "Titles"}
          </p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-[#cdd9e5]">{team.worldcup_appearances}</p>
          <p className="text-xs text-[#768390]">
            {locale === "zh" ? "参赛次数" : "Appearances"}
          </p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-[#3fb950]">{team.ai_impact.overall_score}</p>
          <p className="text-xs text-[#768390]">
            {locale === "zh" ? "AI评分" : "AI Score"}
          </p>
        </div>
      </div>

      {/* Details */}
      {showDetails && (
        <div className="p-4 space-y-4">
          <div>
            <h4 className="text-sm font-semibold text-[#768390] mb-2">
              {locale === "zh" ? "世界杯历史" : "World Cup History"}
            </h4>
            <p className="text-sm text-[#cdd9e5]">{history}</p>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-[#768390] mb-2">
              {locale === "zh" ? "战术风格" : "Tactical Style"}
            </h4>
            <p className="text-sm text-[#cdd9e5]">
              <span className="text-[#58a6ff]">{team.tactical_info.formation}</span>: {style}
            </p>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-[#768390] mb-2">
              {locale === "zh" ? "主要优势" : "Key Strengths"}
            </h4>
            <div className="flex flex-wrap gap-2">
              {strengths.map((strength, index) => (
                <span
                  key={index}
                  className="text-xs bg-[#3fb950]/20 text-[#3fb950] px-2 py-1 rounded"
                >
                  {strength}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
