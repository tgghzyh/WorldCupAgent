"use client";

import { useI18n } from "@/i18n";
import { getTeamById } from "@/knowledge";

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
        <span className="text-white/50">{teamId}</span>
      </div>
    );
  }

  const name = locale === "zh" ? team.names.zh : team.names.en;
  const sizeClasses = { sm: "text-sm", md: "text-base", lg: "text-lg" };

  return (
    <div className="flex items-center gap-2">
      {showFlag && <span className="text-xl">{team.flag_emoji}</span>}
      <span className={`font-medium text-white ${sizeClasses[size]}`}>{name}</span>
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
    ? locale === "zh" ? homeTeam.names.zh : homeTeam.names.en
    : homeTeamId;
  const awayName = awayTeam
    ? locale === "zh" ? awayTeam.names.zh : awayTeam.names.en
    : awayTeamId;

  const confidenceColors = {
    high: "bg-green-500/20 text-green-400 border border-green-500/30",
    medium: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
    low: "bg-red-500/20 text-red-400 border border-red-500/30",
  };

  const confidenceLabels = {
    high: t("confidence.high"),
    medium: t("confidence.medium"),
    low: t("confidence.low"),
  };

  return (
    <div className="w-full max-w-2xl bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 overflow-hidden shadow-2xl shadow-black/20">
      {/* Header */}
      <div className="px-6 py-4 bg-white/5 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#ff6b6b] to-[#ffa502] flex items-center justify-center">
            <span className="text-lg">🏆</span>
          </div>
          <div>
            <p className="text-white/40 text-xs">{locale === "zh" ? "小组赛" : "Group Stage"}</p>
            <p className="text-white font-semibold">{locale === "zh" ? "焦点对决" : "Featured Match"}</p>
          </div>
        </div>
        {confidence && (
          <span className={`text-xs px-3 py-1.5 rounded-full ${confidenceColors[confidence]}`}>
            {confidenceLabels[confidence]}
          </span>
        )}
      </div>

      {/* Teams & Score */}
      <div className="px-8 py-8">
        <div className="flex items-center justify-between">
          {/* Home Team */}
          <div className="flex-1 text-center">
            <div className="text-5xl mb-3">{homeTeam?.flag_emoji || "🏳️"}</div>
            <h3 className="text-xl font-bold text-white mb-1">{homeName}</h3>
            <p className="text-white/40 text-sm">{homeTeam?.short_code || ""}</p>
          </div>

          {/* VS & Probabilities */}
          <div className="px-6 text-center">
            <div className="text-4xl font-bold text-white/20 mb-4">VS</div>
            <div className="text-center space-y-2">
              <div className="text-green-400 font-semibold">
                {Math.round(homeWinProb * 100)}%
              </div>
              <div className="text-yellow-400 text-sm">
                {Math.round(drawProb * 100)}%
              </div>
              <div className="text-red-400 text-sm">
                {Math.round(awayWinProb * 100)}%
              </div>
            </div>
          </div>

          {/* Away Team */}
          <div className="flex-1 text-center">
            <div className="text-5xl mb-3">{awayTeam?.flag_emoji || "🏳️"}</div>
            <h3 className="text-xl font-bold text-white mb-1">{awayName}</h3>
            <p className="text-white/40 text-sm">{awayTeam?.short_code || ""}</p>
          </div>
        </div>

        {/* Probability Bar */}
        <div className="mt-8">
          <div className="flex h-3 rounded-full overflow-hidden bg-white/10">
            <div
              className="bg-gradient-to-r from-green-500 to-emerald-400 transition-all"
              style={{ width: `${homeWinProb * 100}%` }}
            />
            <div
              className="bg-gradient-to-r from-yellow-500 to-amber-400 transition-all"
              style={{ width: `${drawProb * 100}%` }}
            />
            <div
              className="bg-gradient-to-r from-red-500 to-rose-400 transition-all"
              style={{ width: `${awayWinProb * 100}%` }}
            />
          </div>
          <div className="flex justify-between mt-3 text-sm">
            <span className="text-green-400">{t("prediction.home_win")}</span>
            <span className="text-yellow-400">{t("prediction.draw")}</span>
            <span className="text-red-400">{t("prediction.away_win")}</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      {kickoffTime && (
        <div className="px-6 py-4 bg-white/5 border-t border-white/5 flex items-center justify-center gap-2">
          <span className="text-white/40 text-sm">📅</span>
          <span className="text-white/60 text-sm">
            {new Date(kickoffTime).toLocaleString(locale === "zh" ? "zh-CN" : "en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
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
  const { locale } = useI18n();
  const team = getTeamById(teamId);

  if (!team) {
    return (
      <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
        <span className="text-white/50">Team not found: {teamId}</span>
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
    <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden hover:border-white/20 transition-all hover:shadow-xl hover:shadow-black/20 group">
      {/* Header with gradient */}
      <div className="bg-gradient-to-br from-white/5 to-transparent p-6 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="text-5xl group-hover:scale-110 transition-transform">
              {team.flag_emoji}
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">{name}</h3>
              <p className="text-white/50 text-sm">
                <span className="text-white/30">{locale === "zh" ? "绰号" : "Nickname"}:</span> {nickname}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold bg-gradient-to-r from-[#ffd700] to-[#ffa502] bg-clip-text text-transparent">
              {team.ai_impact.overall_score}
            </div>
            <div className="text-white/30 text-xs">{locale === "zh" ? "AI评分" : "AI Score"}</div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="px-6 py-4 grid grid-cols-2 gap-4">
        <div className="bg-white/5 rounded-xl p-3 text-center">
          <p className="text-2xl font-bold text-[#ffd700]">{team.worldcup_titles}</p>
          <p className="text-white/40 text-xs">{locale === "zh" ? "冠军次数" : "Titles"}</p>
        </div>
        <div className="bg-white/5 rounded-xl p-3 text-center">
          <p className="text-2xl font-bold text-white">{team.worldcup_appearances}</p>
          <p className="text-white/40 text-xs">{locale === "zh" ? "参赛次数" : "Appearances"}</p>
        </div>
      </div>

      {/* Details */}
      {showDetails && (
        <div className="px-6 pb-6 space-y-4">
          <div>
            <h4 className="text-xs font-semibold text-white/30 uppercase tracking-wider mb-2">
              {locale === "zh" ? "世界杯历史" : "World Cup History"}
            </h4>
            <p className="text-sm text-white/70">{history}</p>
          </div>
          
          <div>
            <h4 className="text-xs font-semibold text-white/30 uppercase tracking-wider mb-2">
              {locale === "zh" ? "战术风格" : "Tactical Style"}
            </h4>
            <div className="inline-block bg-[#6366f1]/20 text-[#818cf8] px-3 py-1 rounded-full text-sm font-medium">
              {team.tactical_info.formation}
            </div>
            <p className="text-sm text-white/70 mt-2">{style}</p>
          </div>
          
          <div>
            <h4 className="text-xs font-semibold text-white/30 uppercase tracking-wider mb-2">
              {locale === "zh" ? "主要优势" : "Key Strengths"}
            </h4>
            <div className="flex flex-wrap gap-2">
              {strengths.slice(0, 3).map((strength, index) => (
                <span
                  key={index}
                  className="text-xs bg-green-500/20 text-green-400 px-2.5 py-1 rounded-full"
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
