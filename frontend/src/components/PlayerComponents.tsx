"use client";

import { useI18n } from "@/i18n";
import { getPlayerById, getKeyPlayersForTeam, getPlayerName } from "@/knowledge";

interface PlayerCardProps {
  playerId: string;
  showStats?: boolean;
}

export function PlayerCard({ playerId, showStats = true }: PlayerCardProps) {
  const { locale, t } = useI18n();
  const player = getPlayerById(playerId);

  if (!player) {
    return (
      <div className="bg-[#131a24] border border-[#1e2a3a] rounded-lg p-3">
        <span className="text-[#768390]">Player not found: {playerId}</span>
      </div>
    );
  }

  const name = locale === "zh" ? player.names.zh : player.names.en;
  const highlights = locale === "zh" ? player.highlights_zh : player.highlights_en;
  const aiDescription = locale === "zh"
    ? player.ai_impact.description_zh
    : player.ai_impact.description_en;

  return (
    <div className="bg-[#131a24] border border-[#1e2a3a] rounded-lg p-4 hover:border-[#58a6ff]/30 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-semibold text-[#cdd9e5]">{name}</h4>
          <p className="text-sm text-[#768390]">
            {locale === "zh" ? player.position_zh : player.position} • {player.club}
          </p>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-[#58a6ff]">{player.ai_impact.score}</div>
          <div className="text-xs text-[#768390]">
            {locale === "zh" ? "AI评分" : "AI Score"}
          </div>
        </div>
      </div>

      {/* Stats */}
      {showStats && (
        <div className="flex gap-4 mb-3 text-sm">
          <div>
            <span className="text-[#768390]">
              {locale === "zh" ? "出场" : "Caps"}
            </span>
            <span className="ml-2 font-medium text-[#cdd9e5]">{player.national_team_stats.caps}</span>
          </div>
          <div>
            <span className="text-[#768390]">
              {locale === "zh" ? "进球" : "Goals"}
            </span>
            <span className="ml-2 font-medium text-[#cdd9e5]">{player.national_team_stats.goals}</span>
          </div>
          <div>
            <span className="text-[#768390]">
              {locale === "zh" ? "年龄" : "Age"}
            </span>
            <span className="ml-2 font-medium text-[#cdd9e5]">{player.age}</span>
          </div>
        </div>
      )}

      {/* Highlights */}
      <div className="space-y-1">
        {highlights.slice(0, 2).map((highlight, index) => (
          <div key={index} className="flex items-start gap-2 text-xs">
            <span className="text-[#3fb950]">•</span>
            <span className="text-[#cdd9e5]/80">{highlight}</span>
          </div>
        ))}
      </div>

      {/* AI Impact */}
      <div className="mt-3 pt-3 border-t border-[#1e2a3a]">
        <p className="text-xs text-[#768390]">{aiDescription}</p>
      </div>
    </div>
  );
}

interface TeamPlayersProps {
  teamId: string;
  maxPlayers?: number;
}

export function TeamPlayers({ teamId, maxPlayers = 5 }: TeamPlayersProps) {
  const { locale, t } = useI18n();
  const keyPlayers = getKeyPlayersForTeam(teamId);
  const players = keyPlayers.slice(0, maxPlayers);

  if (players.length === 0) {
    return (
      <div className="text-center py-8 text-[#768390]">
        {locale === "zh" ? "暂无球员数据" : "No player data available"}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-[#768390] uppercase tracking-wider">
        {locale === "zh" ? "关键球员" : "Key Players"}
      </h3>
      <div className="grid gap-3">
        {players.map((player) => (
          <PlayerCard key={player.id} playerId={player.id} />
        ))}
      </div>
    </div>
  );
}

interface PlayerHighlightsProps {
  playerId: string;
}

export function PlayerHighlights({ playerId }: PlayerHighlightsProps) {
  const { locale, t } = useI18n();
  const player = getPlayerById(playerId);

  if (!player) return null;

  const highlights = locale === "zh" ? player.highlights_zh : player.highlights_en;

  return (
    <div className="space-y-2">
      {highlights.map((highlight, index) => (
        <div key={index} className="flex items-start gap-3">
          <div className="w-6 h-6 rounded-full bg-[#3fb950]/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span className="text-[#3fb950] text-xs">{index + 1}</span>
          </div>
          <span className="text-sm text-[#cdd9e5]">{highlight}</span>
        </div>
      ))}
    </div>
  );
}
