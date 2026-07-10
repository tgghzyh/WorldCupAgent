export type MatchStatus = "completed" | "live" | "upcoming";

export type Team = {
  id: string;
  name: string;
  code: string;
  flagCode: string;
};

export type TitleContender = {
  team: Team;
  probability: number;
};

export type GroupStanding = {
  team: Team;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDiff: number;
  points: number;
  rank: number;
  qualifiedAs?: "winner" | "runner_up" | "best_third";
};

export type GroupStageGroup = {
  id: string;
  name: string;
  standings: GroupStanding[];
  matches?: BracketMatch[];
};

export type BracketTeamSlot = {
  team: Team;
  probability: number;
  score?: number;
  sourceSeed?: string;
};

export type ConfidenceLevel = "high" | "medium" | "low";

export type ReasoningFactor = {
  id: string;
  type: "fitness" | "tactical" | "injury" | "home" | "form" | "transition";
  label: string;
  description: string;
  weight: number;
};

export type TeamMetricComparison = {
  metric: "recent_form" | "possession" | "xg" | "pressing" | "set_piece";
  label: string;
  homeValue: number;
  awayValue: number;
  unit: string;
};

export type MatchDataSource = {
  label: string;
  href: string;
};

export type MatchDetail = {
  confidence: ConfidenceLevel;
  summary: string;
  reasoningFactors: ReasoningFactor[];
  metricComparison: TeamMetricComparison[];
  dataSources: MatchDataSource[];
  agentTimestamp: string;
  probabilityModel?: {
    homeWinProbability: number;
    drawProbability: number;
    awayWinProbability: number;
    method: string;
  };
  reflection?: {
    verdict: "pass" | "caution" | "inconsistent";
    logicScore: number;
    summary: string;
  };
};

export type BracketMatch = {
  id: string;
  stage:
    | "group"
    | "round_of_32"
    | "round_of_16"
    | "quarter_final"
    | "semi_final"
    | "third_place"
    | "final";
  label: string;
  status: MatchStatus;
  kickoffLabel: string;
  home: BracketTeamSlot;
  away: BracketTeamSlot;
  predictedScore?: string;
  actualScore?: string;
  winnerTeamId?: string;
  advancementRule: string;
  detail: MatchDetail;
};

export type BracketRound = {
  id: BracketMatch["stage"];
  title: string;
  matches: BracketMatch[];
};

export type QualificationRule = {
  slot: string;
  description: string;
};

export type WorldCupBracketData = {
  title: string;
  generatedAt: string;
  titleContenders: TitleContender[];
  groups: GroupStageGroup[];
  bestThirdTeams: GroupStanding[];
  qualificationRules: QualificationRule[];
  rounds: BracketRound[];
};
