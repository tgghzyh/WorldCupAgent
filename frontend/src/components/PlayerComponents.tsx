"use client";

import { useI18n } from "@/i18n";
import { getPlayerById, getKeyPlayersForTeam } from "@/knowledge";

interface PlayerCardProps {
  playerId: string;
  showStats?: boolean;
}

export function PlayerCard({ playerId, showStats = true }: PlayerCardProps) {
  const { locale } = useI18n();
  const player = getPlayerById(playerId);

  if (!player) {
    return (
      <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
        <span className="text-white/50">Player not found: {playerId}</span>
      </div>
    );
  }

  const name = locale === "zh" ? player.names.zh : player.names.en;
  const highlights = locale === "zh" ? player.highlights_zh : player.highlights_en;
  const aiDescription = locale === "zh"
    ? player.ai_impact.description_zh
    : player.ai_impact.description_en;

  const positionColors: Record<string, string> = {
    GK: "from-yellow-500 to-orange-500",
    DEF: "from-blue-500 to-cyan-500",
    MID: "from-green-500 to-emerald-500",
    FWD: "from-red-500 to-pink-500",
  };

  const positionColor = positionColors[player.position_short] || "from-purple-500 to-indigo-500";

  return (
    <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden hover:border-white/20 transition-all hover:shadow-xl hover:shadow-black/20">
      {/* Header */}
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${positionColor} flex items-center justify-center text-white font-bold text-lg shadow-lg`}>
              {player.position_short}
            </div>
            <div>
              <h4 className="font-bold text-white text-lg">{name}</h4>
              <p className="text-white/50 text-sm">{player.club}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold bg-gradient-to-r from-[#a855f7] to-[#6366f1] bg-clip-text text-transparent">
              {player.ai_impact.score}
            </div>
            <div className="text-white/30 text-xs">{locale === "zh" ? "AI评分" : "AI Score"}</div>
          </div>
        </div>

        {/* Stats */}
        {showStats && (
          <div className="flex gap-4 mb-4">
            <div className="flex-1 bg-white/5 rounded-xl p-3 text-center">
              <p className="text-xl font-bold text-white">{player.national_team_stats.caps}</p>
              <p className="text-white/40 text-xs">{locale === "zh" ? "出场" : "Caps"}</p>
            </div>
            <div className="flex-1 bg-white/5 rounded-xl p-3 text-center">
              <p className="text-xl font-bold text-[#ffd700]">{player.national_team_stats.goals}</p>
              <p className="text-white/40 text-xs">{locale === "zh" ? "进球" : "Goals"}</p>
            </div>
            <div className="flex-1 bg-white/5 rounded-xl p-3 text-center">
              <p className="text-xl font-bold text-white">{player.age}</p>
              <p className="text-white/40 text-xs">{locale === "zh" ? "年龄" : "Age"}</p>
            </div>
          </div>
        )}

        {/* Highlights */}
        <div className="space-y-2">
          {highlights.slice(0, 2).map((highlight, index) => (
            <div key={index} className="flex items-start gap-2">
              <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-green-400 text-xs">✓</span>
              </div>
              <span className="text-white/70 text-sm">{highlight}</span>
            </div>
          ))}
        </div>
      </div>

      {/* AI Impact Footer */}
      <div className="px-6 py-4 bg-white/5 border-t border-white/5">
        <p className="text-white/50 text-xs">{aiDescription}</p>
      </div>
    </div>
  );
}

interface TeamPlayersProps {
  teamId: string;
  maxPlayers?: number;
}

export function TeamPlayers({ teamId, maxPlayers = 5 }: TeamPlayersProps) {
  const { locale } = useI18n();
  const keyPlayers = getKeyPlayersForTeam(teamId);
  const players = keyPlayers.slice(0, maxPlayers);

  if (players.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-8 text-center">
        <div className="text-4xl mb-3">👥</div>
        <p className="text-white/50">{locale === "zh" ? "暂无球员数据" : "No player data available"}</p>
      </div>
    );
  }

  return (
    <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden">
      <div className="px-6 py-4 bg-white/5 border-b border-white/5 flex items-center gap-3">
        <span className="text-2xl">👥</span>
        <div>
          <h3 className="text-white font-semibold">{locale === "zh" ? "关键球员" : "Key Players"}</h3>
          <p className="text-white/40 text-xs">{locale === "zh" ? `${players.length} 名球员` : `${players.length} players`}</p>
        </div>
      </div>
      <div className="divide-y divide-white/5">
        {players.map((player) => (
          <PlayerRow key={player.id} player={player} />
        ))}
      </div>
    </div>
  );
}

function PlayerRow({ player }: { player: ReturnType<typeof getPlayerById> }) {
  const { locale } = useI18n();
  
  if (!player) return null;

  const name = locale === "zh" ? player.names.zh : player.names.en;

  return (
    <div className="px-6 py-4 flex items-center gap-4 hover:bg-white/5 transition-colors">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#a855f7] to-[#6366f1] flex items-center justify-center text-white font-bold text-sm">
        {player.position_short}
      </div>
      <div className="flex-1">
        <p className="text-white font-medium">{name}</p>
        <p className="text-white/40 text-xs">{player.club}</p>
      </div>
      <div className="text-right">
        <p className="text-[#ffd700] font-bold">{player.national_team_stats.goals} {locale === "zh" ? "球" : "G"}</p>
        <p className="text-white/30 text-xs">{player.national_team_stats.caps} {locale === "zh" ? "场" : "Caps"}</p>
      </div>
    </div>
  );
}

interface PlayerHighlightsProps {
  playerId: string;
}

export function PlayerHighlights({ playerId }: PlayerHighlightsProps) {
  const { locale } = useI18n();
  const player = getPlayerById(playerId);

  if (!player) return null;

  const highlights = locale === "zh" ? player.highlights_zh : player.highlights_en;

  return (
    <div className="space-y-3">
      {highlights.map((highlight, index) => (
        <div key={index} className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#a855f7] to-[#6366f1] flex items-center justify-center text-white text-sm font-bold">
            {index + 1}
          </div>
          <span className="text-white/80 text-sm pt-1">{highlight}</span>
        </div>
      ))}
    </div>
  );
}
