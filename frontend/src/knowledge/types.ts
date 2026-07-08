/**
 * Football Knowledge Layer - Type Definitions
 * Provides type-safe access to team, player, and coach knowledge
 */

import { Locale } from "@/i18n";

// Team Types
export interface TeamNames {
  zh: string;
  en: string;
}

export interface TeamNickname {
  zh: string;
  en: string;
}

export interface TournamentHistory {
  zh: string;
  en: string;
}

export interface TacticalInfo {
  formation: string;
  style_zh: string;
  style_en: string;
  key_strengths_zh: string[];
  key_strengths_en: string[];
  potential_weaknesses_zh?: string[];
  potential_weaknesses_en?: string[];
}

export interface TeamAIImpact {
  overall_score: number;
  description_zh: string;
  description_en: string;
}

export interface Team {
  id: string;
  names: TeamNames;
  flag_emoji: string;
  short_code: string;
  fifa_code: string;
  confederation: string;
  group: string;
  worldcup_appearances: number;
  worldcup_titles: number;
  tournament_history: TournamentHistory;
  nickname: TeamNickname;
  tactical_info: TacticalInfo;
  key_players: string[];
  coach_id: string;
  ai_impact: TeamAIImpact;
}

// Player Types
export interface PlayerNationality {
  zh: string;
  en: string;
}

export interface PlayerNationalTeamStats {
  caps: number;
  goals: number;
}

export interface PlayerAIImpact {
  score: number;
  description_zh: string;
  description_en: string;
}

export interface Player {
  id: string;
  names: TeamNames;
  team_id: string;
  position: string;
  position_short: string;
  position_zh: string;
  age: number;
  club: string;
  nationality: PlayerNationality;
  national_team_stats: PlayerNationalTeamStats;
  highlights_zh: string[];
  highlights_en: string[];
  ai_impact: PlayerAIImpact;
}

// Coach Types
export interface CoachNationality {
  zh: string;
  en: string;
}

export interface CoachingTactical {
  formation: string;
  philosophy_zh: string;
  philosophy_en: string;
}

export interface Coach {
  id: string;
  names: TeamNames;
  team_id: string;
  nationality: CoachNationality;
  age: number;
  tenure_since: string;
  coaching_tactical: CoachingTactical;
  achievements_zh: string[];
  achievements_en: string[];
  ai_tactical_score: number;
}

// Knowledge Layer Types
export interface TeamsKnowledge {
  _metadata: {
    version: string;
    generated_at: string;
    description: string;
    locale: string;
  };
  teams: Record<string, Team>;
}

export interface PlayersKnowledge {
  _metadata: {
    version: string;
    generated_at: string;
    description: string;
  };
  players: Record<string, Player>;
}

export interface CoachesKnowledge {
  _metadata: {
    version: string;
    generated_at: string;
    description: string;
  };
  coaches: Record<string, Coach>;
}

// Knowledge Accessor Types
export interface KnowledgeAccessor<T> {
  getById: (id: string) => T | undefined;
  getByTeam: (teamId: string) => T[];
  getAll: () => T[];
}

export interface TeamKnowledgeAccessor extends KnowledgeAccessor<Team> {
  getByName: (name: string) => Team | undefined;
  getByGroup: (group: string) => Team[];
  getByConfederation: (confederation: string) => Team[];
  getTopTeams: (count: number) => Team[];
}

export interface PlayerKnowledgeAccessor extends KnowledgeAccessor<Player> {
  getByName: (name: string) => Player | undefined;
  getByPosition: (position: string) => Player[];
  getTopPlayers: (count: number) => Player[];
}

export interface CoachKnowledgeAccessor extends KnowledgeAccessor<Coach> {
  getByName: (name: string) => Coach | undefined;
}

// Localized Content Helper
export interface LocalizedContent {
  getName: (locale: Locale) => string;
  getLocalizedString: (field: string, locale: Locale) => string | string[];
}
