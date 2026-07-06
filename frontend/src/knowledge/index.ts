/**
 * Football Knowledge Layer - Main Index
 * Provides hooks and utilities for accessing team, player, and coach knowledge
 */

"use client";

import { useMemo, useCallback, useContext, createContext } from "react";
import { useI18n, Locale } from "@/i18n";
import teamsData from "./teams_knowledge.json";
import playersData from "./players_knowledge.json";
import coachesData from "./coaches_knowledge.json";
import type {
  Team,
  Player,
  Coach,
  TeamsKnowledge,
  PlayersKnowledge,
  CoachesKnowledge,
  TeamKnowledgeAccessor,
  PlayerKnowledgeAccessor,
  CoachKnowledgeAccessor,
} from "./types";

// Cast JSON data to typed interfaces
const teamsKnowledge = teamsData as TeamsKnowledge;
const playersKnowledge = playersData as PlayersKnowledge;
const coachesKnowledge = coachesData as CoachesKnowledge;

// ============================================
// TEAM KNOWLEDGE
// ============================================

/**
 * Get team by ID
 */
export function getTeamById(id: string): Team | undefined {
  return teamsKnowledge.teams[id.toLowerCase()];
}

/**
 * Get team by English or Chinese name
 */
export function getTeamByName(name: string): Team | undefined {
  const normalizedName = name.toLowerCase();
  return Object.values(teamsKnowledge.teams).find(
    (team) =>
      team.names.en.toLowerCase() === normalizedName ||
      team.names.zh === name ||
      team.id.toLowerCase() === normalizedName ||
      team.short_code.toLowerCase() === normalizedName
  );
}

/**
 * Get teams by group letter (A-L)
 */
export function getTeamsByGroup(group: string): Team[] {
  const normalizedGroup = group.toUpperCase();
  return Object.values(teamsKnowledge.teams).filter(
    (team) => team.group === normalizedGroup
  );
}

/**
 * Get teams by confederation
 */
export function getTeamsByConfederation(confederation: string): Team[] {
  return Object.values(teamsKnowledge.teams).filter(
    (team) => team.confederation.toLowerCase() === confederation.toLowerCase()
  );
}

/**
 * Get all teams
 */
export function getAllTeams(): Team[] {
  return Object.values(teamsKnowledge.teams);
}

/**
 * Get top teams by AI impact score
 */
export function getTopTeams(count: number = 10): Team[] {
  return Object.values(teamsKnowledge.teams)
    .filter((team) => team.ai_impact?.overall_score !== undefined)
    .sort((a, b) => b.ai_impact.overall_score - a.ai_impact.overall_score)
    .slice(0, count);
}

/**
 * Get localized team name
 */
export function getTeamName(teamId: string, locale: Locale): string {
  const team = getTeamById(teamId);
  if (!team) return teamId;
  return locale === "zh" ? team.names.zh : team.names.en;
}

/**
 * Get team flag emoji
 */
export function getTeamFlag(teamId: string): string {
  const team = getTeamById(teamId);
  return team?.flag_emoji || "🏳️";
}

// ============================================
// PLAYER KNOWLEDGE
// ============================================

/**
 * Get player by ID
 */
export function getPlayerById(id: string): Player | undefined {
  return playersKnowledge.players[id.toLowerCase()];
}

/**
 * Get player by English or Chinese name
 */
export function getPlayerByName(name: string): Player | undefined {
  const normalizedName = name.toLowerCase();
  return Object.values(playersKnowledge.players).find(
    (player) =>
      player.names.en.toLowerCase() === normalizedName ||
      player.names.zh === name ||
      player.id.toLowerCase() === normalizedName
  );
}

/**
 * Get players by team ID
 */
export function getPlayersByTeam(teamId: string): Player[] {
  return Object.values(playersKnowledge.players).filter(
    (player) => player.team_id === teamId.toLowerCase()
  );
}

/**
 * Get key players for a team (from team's key_players list)
 */
export function getKeyPlayersForTeam(teamId: string): Player[] {
  const team = getTeamById(teamId);
  if (!team) return [];
  
  return team.key_players
    .map((playerId) => getPlayerById(playerId))
    .filter((player): player is Player => player !== undefined);
}

/**
 * Get all players
 */
export function getAllPlayers(): Player[] {
  return Object.values(playersKnowledge.players);
}

/**
 * Get top players by AI impact score
 */
export function getTopPlayers(count: number = 10): Player[] {
  return Object.values(playersKnowledge.players)
    .sort((a, b) => b.ai_impact.score - a.ai_impact.score)
    .slice(0, count);
}

/**
 * Get localized player name
 */
export function getPlayerName(playerId: string, locale: Locale): string {
  const player = getPlayerById(playerId);
  if (!player) return playerId;
  return locale === "zh" ? player.names.zh : player.names.en;
}

// ============================================
// COACH KNOWLEDGE
// ============================================

/**
 * Get coach by ID
 */
export function getCoachById(id: string): Coach | undefined {
  return coachesKnowledge.coaches[id.toLowerCase()];
}

/**
 * Get coach for a team
 */
export function getCoachForTeam(teamId: string): Coach | undefined {
  const team = getTeamById(teamId);
  if (!team) return undefined;
  return getCoachById(team.coach_id);
}

/**
 * Get all coaches
 */
export function getAllCoaches(): Coach[] {
  return Object.values(coachesKnowledge.coaches);
}

/**
 * Get localized coach name
 */
export function getCoachName(coachId: string, locale: Locale): string {
  const coach = getCoachById(coachId);
  if (!coach) return coachId;
  return locale === "zh" ? coach.names.zh : coach.names.en;
}

// ============================================
// REACT HOOKS
// ============================================

/**
 * Hook to access team knowledge
 */
export function useTeamKnowledge(): TeamKnowledgeAccessor<Team> {
  const teams = useMemo(() => getAllTeams(), []);
  
  return useMemo(
    () => ({
      getById: (id: string) => getTeamById(id),
      getByTeam: (teamId: string) => getPlayersByTeam(teamId) as unknown as Team[],
      getAll: () => teams,
      getByName: (name: string) => getTeamByName(name),
      getByGroup: (group: string) => getTeamsByGroup(group),
      getByConfederation: (confederation: string) =>
        getTeamsByConfederation(confederation),
      getTopTeams: (count: number) => getTopTeams(count),
    }),
    [teams]
  );
}

/**
 * Hook to access player knowledge
 */
export function usePlayerKnowledge(): PlayerKnowledgeAccessor<Player> {
  const players = useMemo(() => getAllPlayers(), []);
  
  return useMemo(
    () => ({
      getById: (id: string) => getPlayerById(id),
      getByTeam: (teamId: string) => getPlayersByTeam(teamId),
      getAll: () => players,
      getByName: (name: string) => getPlayerByName(name),
      getByPosition: (position: string) =>
        players.filter((p) => p.position.toLowerCase() === position.toLowerCase()),
      getTopPlayers: (count: number) => getTopPlayers(count),
    }),
    [players]
  );
}

/**
 * Hook to access coach knowledge
 */
export function useCoachKnowledge(): CoachKnowledgeAccessor<Coach> {
  const coaches = useMemo(() => getAllCoaches(), []);
  
  return useMemo(
    () => ({
      getById: (id: string) => getCoachById(id),
      getByTeam: (teamId: string) =>
        [getCoachForTeam(teamId)].filter((c): c is Coach => c !== undefined),
      getAll: () => coaches,
      getByName: (name: string) => {
        const normalizedName = name.toLowerCase();
        return coaches.find(
          (coach) =>
            coach.names.en.toLowerCase() === normalizedName ||
            coach.names.zh === name
        );
      },
    }),
    [coaches]
  );
}

/**
 * Hook to get localized team info
 */
export function useTeamInfo(teamId: string) {
  const { locale } = useI18n();
  
  return useMemo(() => {
    const team = getTeamById(teamId);
    if (!team) return null;
    
    return {
      id: team.id,
      name: locale === "zh" ? team.names.zh : team.names.en,
      flag: team.flag_emoji,
      group: team.group,
      shortCode: team.short_code,
      nickname: locale === "zh" ? team.nickname.zh : team.nickname.en,
      confederation: team.confederation,
      worldcupTitles: team.worldcup_titles,
      worldcupAppearances: team.worldcup_appearances,
      tournamentHistory:
        locale === "zh" ? team.tournament_history.zh : team.tournament_history.en,
      formation: team.tactical_info.formation,
      style: locale === "zh" ? team.tactical_info.style_zh : team.tactical_info.style_en,
      strengths:
        locale === "zh"
          ? team.tactical_info.key_strengths_zh
          : team.tactical_info.key_strengths_en,
      aiScore: team.ai_impact.overall_score,
      aiDescription:
        locale === "zh" ? team.ai_impact.description_zh : team.ai_impact.description_en,
    };
  }, [teamId, locale]);
}

/**
 * Hook to get localized player info
 */
export function usePlayerInfo(playerId: string) {
  const { locale } = useI18n();
  
  return useMemo(() => {
    const player = getPlayerById(playerId);
    if (!player) return null;
    
    return {
      id: player.id,
      name: locale === "zh" ? player.names.zh : player.names.en,
      teamId: player.team_id,
      position: player.position,
      positionShort: player.position_short,
      positionZh: player.position_zh,
      age: player.age,
      club: player.club,
      nationality:
        locale === "zh" ? player.nationality.zh : player.nationality.en,
      caps: player.national_team_stats.caps,
      goals: player.national_team_stats.goals,
      highlights:
        locale === "zh" ? player.highlights_zh : player.highlights_en,
      aiScore: player.ai_impact.score,
      aiDescription:
        locale === "zh"
          ? player.ai_impact.description_zh
          : player.ai_impact.description_en,
    };
  }, [playerId, locale]);
}

/**
 * Hook to get localized coach info
 */
export function useCoachInfo(coachId: string) {
  const { locale } = useI18n();
  
  return useMemo(() => {
    const coach = getCoachById(coachId);
    if (!coach) return null;
    
    return {
      id: coach.id,
      name: locale === "zh" ? coach.names.zh : coach.names.en,
      teamId: coach.team_id,
      nationality:
        locale === "zh" ? coach.nationality.zh : coach.nationality.en,
      age: coach.age,
      tenureSince: coach.tenure_since,
      formation: coach.coaching_tactical.formation,
      philosophy:
        locale === "zh"
          ? coach.coaching_tactical.philosophy_zh
          : coach.coaching_tactical.philosophy_en,
      achievements:
        locale === "zh" ? coach.achievements_zh : coach.achievements_en,
      tacticalScore: coach.ai_tactical_score,
    };
  }, [coachId, locale]);
}

/**
 * Hook to get team with related data (players, coach)
 */
export function useTeamWithRelations(teamId: string) {
  const { locale } = useI18n();
  
  return useMemo(() => {
    const team = getTeamById(teamId);
    if (!team) return null;
    
    const coach = getCoachById(team.coach_id);
    const keyPlayers = getKeyPlayersForTeam(teamId);
    
    return {
      team: {
        id: team.id,
        name: locale === "zh" ? team.names.zh : team.names.en,
        flag: team.flag_emoji,
        group: team.group,
        nickname: locale === "zh" ? team.nickname.zh : team.nickname.en,
        confederation: team.confederation,
        worldcupTitles: team.worldcup_titles,
        worldcupAppearances: team.worldcup_appearances,
        tournamentHistory:
          locale === "zh"
            ? team.tournament_history.zh
            : team.tournament_history.en,
        formation: team.tactical_info.formation,
        style: locale === "zh" ? team.tactical_info.style_zh : team.tactical_info.style_en,
        strengths:
          locale === "zh"
            ? team.tactical_info.key_strengths_zh
            : team.tactical_info.key_strengths_en,
        aiScore: team.ai_impact.overall_score,
        aiDescription:
          locale === "zh"
            ? team.ai_impact.description_zh
            : team.ai_impact.description_en,
      },
      coach: coach
        ? {
            id: coach.id,
            name: locale === "zh" ? coach.names.zh : coach.names.en,
            nationality:
              locale === "zh" ? coach.nationality.zh : coach.nationality.en,
            age: coach.age,
            tenureSince: coach.tenure_since,
            formation: coach.coaching_tactical.formation,
            philosophy:
              locale === "zh"
                ? coach.coaching_tactical.philosophy_zh
                : coach.coaching_tactical.philosophy_en,
            achievements:
              locale === "zh" ? coach.achievements_zh : coach.achievements_en,
            tacticalScore: coach.ai_tactical_score,
          }
        : null,
      players: keyPlayers.map((player) => ({
        id: player.id,
        name: locale === "zh" ? player.names.zh : player.names.en,
        position: player.position,
        positionShort: player.position_short,
        age: player.age,
        club: player.club,
        caps: player.national_team_stats.caps,
        goals: player.national_team_stats.goals,
        highlights:
          locale === "zh" ? player.highlights_zh : player.highlights_en,
        aiScore: player.ai_impact.score,
      })),
    };
  }, [teamId, locale]);
}

// ============================================
// MATCH PREDICTION HELPERS
// ============================================

/**
 * Get team comparison data for a match
 */
export function getTeamComparison(homeTeamId: string, awayTeamId: string) {
  const homeTeam = getTeamById(homeTeamId);
  const awayTeam = getTeamById(awayTeamId);
  
  if (!homeTeam || !awayTeam) return null;
  
  return {
    home: {
      id: homeTeam.id,
      name: homeTeam.names.en,
      nameZh: homeTeam.names.zh,
      flag: homeTeam.flag_emoji,
      aiScore: homeTeam.ai_impact.overall_score,
      worldcupTitles: homeTeam.worldcup_titles,
      group: homeTeam.group,
    },
    away: {
      id: awayTeam.id,
      name: awayTeam.names.en,
      nameZh: awayTeam.names.zh,
      flag: awayTeam.flag_emoji,
      aiScore: awayTeam.ai_impact.overall_score,
      worldcupTitles: awayTeam.worldcup_titles,
      group: awayTeam.group,
    },
    comparison: {
      aiDiff: homeTeam.ai_impact.overall_score - awayTeam.ai_impact.overall_score,
      titlesDiff: homeTeam.worldcup_titles - awayTeam.worldcup_titles,
    },
  };
}

// ============================================
// EXPORTS
// ============================================

export { teamsKnowledge, playersKnowledge, coachesKnowledge };
export type { Team, Player, Coach } from "./types";
