import type {
  BracketMatch,
  BracketRound,
  ConfidenceLevel,
  GroupStageGroup,
  GroupStanding,
  MatchDetail,
  Team,
  WorldCupBracketData,
} from "./types";

const teams: Team[] = [
  ["arg", "Argentina", "ARG", "🇦🇷"], ["mex", "Mexico", "MEX", "🇲🇽"], ["ecu", "Ecuador", "ECU", "🇪🇨"], ["jam", "Jamaica", "JAM", "🇯🇲"],
  ["usa", "United States", "USA", "🇺🇸"], ["uru", "Uruguay", "URU", "🇺🇾"], ["kor", "South Korea", "KOR", "🇰🇷"], ["gha", "Ghana", "GHA", "🇬🇭"],
  ["bra", "Brazil", "BRA", "🇧🇷"], ["jpn", "Japan", "JPN", "🇯🇵"], ["sco", "Scotland", "SCO", "🏴󠁧󠁢󠁳󠁣󠁴󠁿"], ["egy", "Egypt", "EGY", "🇪🇬"],
  ["fra", "France", "FRA", "🇫🇷"], ["sen", "Senegal", "SEN", "🇸🇳"], ["can", "Canada", "CAN", "🇨🇦"], ["qat", "Qatar", "QAT", "🇶🇦"],
  ["esp", "Spain", "ESP", "🇪🇸"], ["mar", "Morocco", "MAR", "🇲🇦"], ["crc", "Costa Rica", "CRC", "🇨🇷"], ["nz", "New Zealand", "NZL", "🇳🇿"],
  ["por", "Portugal", "POR", "🇵🇹"], ["col", "Colombia", "COL", "🇨🇴"], ["aus", "Australia", "AUS", "🇦🇺"], ["tun", "Tunisia", "TUN", "🇹🇳"],
  ["eng", "England", "ENG", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"], ["civ", "Ivory Coast", "CIV", "🇨🇮"], ["per", "Peru", "PER", "🇵🇪"], ["wal", "Wales", "WAL", "🏴󠁧󠁢󠁷󠁬󠁳󠁿"],
  ["ned", "Netherlands", "NED", "🇳🇱"], ["srb", "Serbia", "SRB", "🇷🇸"], ["pan", "Panama", "PAN", "🇵🇦"], ["alg", "Algeria", "ALG", "🇩🇿"],
  ["ger", "Germany", "GER", "🇩🇪"], ["cro", "Croatia", "CRO", "🇭🇷"], ["rsa", "South Africa", "RSA", "🇿🇦"], ["bol", "Bolivia", "BOL", "🇧🇴"],
  ["ita", "Italy", "ITA", "🇮🇹"], ["den", "Denmark", "DEN", "🇩🇰"], ["cmr", "Cameroon", "CMR", "🇨🇲"], ["par", "Paraguay", "PAR", "🇵🇾"],
  ["bel", "Belgium", "BEL", "🇧🇪"], ["swe", "Sweden", "SWE", "🇸🇪"], ["nga", "Nigeria", "NGA", "🇳🇬"], ["bf", "Burkina Faso", "BFA", "🇧🇫"],
  ["aut", "Austria", "AUT", "🇦🇹"], ["irn", "Iran", "IRN", "🇮🇷"], ["gre", "Greece", "GRE", "🇬🇷"], ["zam", "Zambia", "ZAM", "🇿🇲"],
].map(([id, name, code, flag]) => ({ id, name, code, flag }));

const teamById = Object.fromEntries(teams.map((team) => [team.id, team]));

function standing(teamId: string, rank: number, points: number, gd: number): GroupStanding {
  return {
    team: teamById[teamId],
    played: 3,
    won: rank === 1 ? 2 : rank === 2 ? 1 : 1,
    drawn: rank === 4 ? 0 : 1,
    lost: rank === 1 ? 0 : rank === 2 ? 1 : 2,
    goalsFor: Math.max(2, 7 - rank + Math.max(gd, 0)),
    goalsAgainst: Math.max(1, 4 - gd),
    goalDiff: gd,
    points,
    rank,
    qualifiedAs: rank === 1 ? "winner" : rank === 2 ? "runner_up" : undefined,
  };
}

const groupTeamIds = [
  ["arg", "mex", "ecu", "jam"],
  ["usa", "uru", "kor", "gha"],
  ["bra", "jpn", "sco", "egy"],
  ["fra", "sen", "can", "qat"],
  ["esp", "mar", "crc", "nz"],
  ["por", "col", "aus", "tun"],
  ["eng", "civ", "per", "wal"],
  ["ned", "srb", "pan", "alg"],
  ["ger", "cro", "rsa", "bol"],
  ["ita", "den", "cmr", "par"],
  ["bel", "swe", "nga", "bf"],
  ["aut", "irn", "gre", "zam"],
];

export const mockGroups: GroupStageGroup[] = groupTeamIds.map((ids, index) => {
  const letter = String.fromCharCode(65 + index);
  const rows = [
    standing(ids[0], 1, 7, 4),
    standing(ids[1], 2, 5, 2),
    standing(ids[2], 3, 4, index % 2 === 0 ? 1 : 0),
    standing(ids[3], 4, 0, -6),
  ];
  return { id: letter, name: `Group ${letter}`, standings: rows };
});

const bestThirdIds = ["ecu", "sco", "crc", "aus", "per", "pan", "rsa", "cmr"];

for (const group of mockGroups) {
  const third = group.standings[2];
  if (bestThirdIds.includes(third.team.id)) {
    third.qualifiedAs = "best_third";
  }
}

function slot(teamId: string, probability: number, sourceSeed: string, score?: number) {
  return { team: teamById[teamId], probability, sourceSeed, score };
}

function confidenceFromProbability(homeProbability: number, awayProbability: number): ConfidenceLevel {
  const spread = Math.abs(homeProbability - awayProbability);
  if (spread >= 0.32) return "high";
  if (spread >= 0.14) return "medium";
  return "low";
}

function detail(home: ReturnType<typeof slot>, away: ReturnType<typeof slot>, id: string): MatchDetail {
  const confidence = confidenceFromProbability(home.probability, away.probability);
  const homeEdge = Math.max(0.08, Math.min(0.88, home.probability));
  const awayEdge = Math.max(0.08, Math.min(0.88, away.probability));

  return {
    confidence,
    reasoningFactors: [
      {
        id: `${id}-fitness`,
        type: "fitness",
        label: "Fitness advantage",
        description: `${home.team.name} projects fresher in the final 30 minutes based on rotation depth and travel load.`,
        weight: Math.min(0.88, homeEdge + 0.08),
      },
      {
        id: `${id}-tactical`,
        type: "tactical",
        label: "Tactical matchup",
        description: `${home.team.name}'s midfield structure can limit ${away.team.name}'s preferred central progression lanes.`,
        weight: Math.max(0.34, homeEdge - 0.02),
      },
      {
        id: `${id}-injury`,
        type: "injury",
        label: "Injury impact",
        description: `${away.team.name} carries a slightly higher lineup uncertainty signal in the current mock forecast.`,
        weight: 0.42,
      },
      {
        id: `${id}-home`,
        type: "home",
        label: "Venue effect",
        description: "Crowd and travel context add a small but visible tilt to the higher-seeded side.",
        weight: 0.36,
      },
      {
        id: `${id}-form`,
        type: "form",
        label: "Recent form",
        description: `${home.team.name} has the stronger recent five-match trend in the Agent baseline.`,
        weight: Math.max(0.28, homeEdge - awayEdge + 0.38),
      },
    ],
    metricComparison: [
      {
        metric: "recent_form",
        label: "Recent 5",
        homeValue: Math.round(45 + home.probability * 45),
        awayValue: Math.round(45 + away.probability * 45),
        unit: "score",
      },
      {
        metric: "possession",
        label: "Possession",
        homeValue: Math.round(47 + home.probability * 18),
        awayValue: Math.round(47 + away.probability * 18),
        unit: "%",
      },
      {
        metric: "xg",
        label: "xG",
        homeValue: Number((0.8 + home.probability * 1.6).toFixed(2)),
        awayValue: Number((0.8 + away.probability * 1.6).toFixed(2)),
        unit: "xG",
      },
      {
        metric: "pressing",
        label: "Pressing",
        homeValue: Math.round(40 + home.probability * 48),
        awayValue: Math.round(40 + away.probability * 48),
        unit: "idx",
      },
      {
        metric: "set_piece",
        label: "Set pieces",
        homeValue: Math.round(35 + home.probability * 40),
        awayValue: Math.round(35 + away.probability * 40),
        unit: "idx",
      },
    ],
    dataSources: [
      { label: "FIFA match schedule", href: "https://www.fifa.com/" },
      { label: "EloRatings baseline", href: "https://www.eloratings.net/" },
      { label: "Agent snapshot mock", href: "/data/snapshots/latest.json" },
    ],
    agentTimestamp: "2026-07-07T09:00:00Z",
  };
}

function match(
  id: string,
  label: string,
  home: ReturnType<typeof slot>,
  away: ReturnType<typeof slot>,
  status: BracketMatch["status"],
  advancementRule: string,
  predictedScore = "2-1",
  actualScore?: string,
  winnerTeamId?: string
): BracketMatch {
  return {
    id,
    stage: "round_of_32",
    label,
    status,
    kickoffLabel: status === "completed" ? "FT" : status === "live" ? "63'" : "2026 KO",
    home,
    away,
    predictedScore,
    actualScore,
    winnerTeamId,
    advancementRule,
    detail: detail(home, away, id),
  };
}

const r32 = [
  match("r32-01", "1A vs 3C/E/F/H/I", slot("arg", 0.72, "1A", 2), slot("sco", 0.18, "Best 3C", 0), "completed", "Group winner A faces an eligible best third-place team.", "2-0", "2-0", "arg"),
  match("r32-02", "2B vs 2C", slot("uru", 0.52, "2B"), slot("jpn", 0.31, "2C"), "upcoming", "Runner-up derby fixed by 2026 bracket."),
  match("r32-03", "1D vs 3B/E/F/I/J", slot("fra", 0.66, "1D"), slot("ecu", 0.21, "Best 3A"), "live", "Group winner D draws one best third-place team."),
  match("r32-04", "1E vs 2F", slot("esp", 0.59, "1E"), slot("col", 0.24, "2F"), "upcoming", "Group E winner crosses with Group F runner-up."),
  match("r32-05", "1B vs 3E/F/G/I/J", slot("usa", 0.43, "1B"), slot("crc", 0.29, "Best 3E"), "upcoming", "Host group winner path with best third-place slot."),
  match("r32-06", "1C vs 2F", slot("bra", 0.61, "1C"), slot("col", 0.23, "2F"), "upcoming", "Group winner C crosses with a runner-up slot."),
  match("r32-07", "1F vs 2C", slot("por", 0.57, "1F"), slot("jpn", 0.25, "2C"), "upcoming", "Fixed 2026 runner-up crossover."),
  match("r32-08", "2A vs 2B", slot("mex", 0.49, "2A"), slot("uru", 0.33, "2B"), "upcoming", "Runner-up derby fixed by public bracket shape."),
  match("r32-09", "1G vs 3A/E/H/I/J", slot("eng", 0.62, "1G"), slot("pan", 0.18, "Best 3H"), "upcoming", "Winner G receives eligible best third."),
  match("r32-10", "1H vs 2J", slot("ned", 0.55, "1H"), slot("den", 0.26, "2J"), "upcoming", "Group H winner crosses to Group J runner-up."),
  match("r32-11", "1I vs 3C/D/F/G/H", slot("ger", 0.6, "1I"), slot("aus", 0.19, "Best 3F"), "upcoming", "Winner I receives eligible best third."),
  match("r32-12", "1J vs 2H", slot("ita", 0.5, "1J"), slot("srb", 0.3, "2H"), "upcoming", "Fixed winner-runner-up crossover."),
  match("r32-13", "1K vs 3D/E/I/J/L", slot("bel", 0.53, "1K"), slot("rsa", 0.23, "Best 3I"), "upcoming", "Winner K receives eligible best third."),
  match("r32-14", "1L vs 3E/H/I/J/K", slot("aut", 0.48, "1L"), slot("cmr", 0.3, "Best 3J"), "upcoming", "Winner L receives eligible best third."),
  match("r32-15", "2E vs 2I", slot("mar", 0.42, "2E"), slot("cro", 0.36, "2I"), "upcoming", "Runner-up derby fixed by 2026 bracket."),
  match("r32-16", "2K vs 2L", slot("swe", 0.38, "2K"), slot("irn", 0.34, "2L"), "upcoming", "Runner-up derby fixed by 2026 bracket."),
];

function nextRoundMatch(
  id: string,
  stage: BracketMatch["stage"],
  label: string,
  homeId: string,
  awayId: string,
  homeProb: number,
  awayProb: number
): BracketMatch {
  return {
    id,
    stage,
    label,
    status: "upcoming",
    kickoffLabel: "Projected",
    home: slot(homeId, homeProb, "Projected winner"),
    away: slot(awayId, awayProb, "Projected winner"),
    predictedScore: homeProb >= awayProb ? "2-1" : "1-2",
    advancementRule: "Projected from the previous knockout branch.",
    winnerTeamId: homeProb >= awayProb ? homeId : awayId,
    detail: detail(slot(homeId, homeProb, "Projected winner"), slot(awayId, awayProb, "Projected winner"), id),
  };
}

const rounds: BracketRound[] = [
  { id: "round_of_32", title: "Round of 32", matches: r32 },
  {
    id: "round_of_16",
    title: "Round of 16",
    matches: [
      nextRoundMatch("r16-01", "round_of_16", "W R32-01 vs W R32-02", "arg", "uru", 0.64, 0.24),
      nextRoundMatch("r16-02", "round_of_16", "W R32-03 vs W R32-04", "fra", "esp", 0.46, 0.39),
      nextRoundMatch("r16-03", "round_of_16", "W R32-05 vs W R32-06", "usa", "bra", 0.28, 0.55),
      nextRoundMatch("r16-04", "round_of_16", "W R32-07 vs W R32-08", "por", "mex", 0.53, 0.29),
      nextRoundMatch("r16-05", "round_of_16", "W R32-09 vs W R32-10", "eng", "ned", 0.48, 0.34),
      nextRoundMatch("r16-06", "round_of_16", "W R32-11 vs W R32-12", "ger", "ita", 0.51, 0.31),
      nextRoundMatch("r16-07", "round_of_16", "W R32-13 vs W R32-14", "bel", "aut", 0.44, 0.36),
      nextRoundMatch("r16-08", "round_of_16", "W R32-15 vs W R32-16", "cro", "swe", 0.43, 0.35),
    ],
  },
  {
    id: "quarter_final",
    title: "Quarter-finals",
    matches: [
      nextRoundMatch("qf-01", "quarter_final", "Projected QF 1", "arg", "fra", 0.52, 0.36),
      nextRoundMatch("qf-02", "quarter_final", "Projected QF 2", "bra", "por", 0.5, 0.34),
      nextRoundMatch("qf-03", "quarter_final", "Projected QF 3", "eng", "ger", 0.43, 0.39),
      nextRoundMatch("qf-04", "quarter_final", "Projected QF 4", "bel", "cro", 0.4, 0.37),
    ],
  },
  {
    id: "semi_final",
    title: "Semi-finals",
    matches: [
      nextRoundMatch("sf-01", "semi_final", "Projected SF 1", "arg", "bra", 0.51, 0.38),
      nextRoundMatch("sf-02", "semi_final", "Projected SF 2", "ger", "bel", 0.46, 0.35),
    ],
  },
  {
    id: "third_place",
    title: "Third place",
    matches: [nextRoundMatch("tp-01", "third_place", "Semi-final losers", "bra", "bel", 0.47, 0.36)],
  },
  {
    id: "final",
    title: "Final",
    matches: [nextRoundMatch("final-01", "final", "World Cup Final", "arg", "ger", 0.49, 0.37)],
  },
];

export const worldCupBracketMock: WorldCupBracketData = {
  title: "2026 World Cup Champion Prediction Agent",
  generatedAt: "2026-07-07 09:00 UTC",
  titleContenders: [
    { team: teamById.arg, probability: 0.49 },
    { team: teamById.ger, probability: 0.37 },
    { team: teamById.bra, probability: 0.31 },
    { team: teamById.fra, probability: 0.28 },
    { team: teamById.eng, probability: 0.24 },
  ],
  groups: mockGroups,
  bestThirdTeams: mockGroups.map((group) => group.standings[2]).filter((row) => row.qualifiedAs === "best_third"),
  qualificationRules: [
    { slot: "1st", description: "All 12 group winners qualify directly to the Round of 32." },
    { slot: "2nd", description: "All 12 group runners-up qualify directly to the Round of 32." },
    { slot: "3rd", description: "The 8 best third-place teams complete the 32-team knockout field." },
  ],
  rounds,
};
