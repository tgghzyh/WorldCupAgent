import type { Snapshot } from "@/lib/tournament/types";
import type {
  BracketMatch,
  BracketRound,
  BracketTeamSlot,
  ConfidenceLevel,
  GroupStageGroup,
  GroupStanding,
  MatchDetail,
  Team,
  TitleContender,
  WorldCupBracketData,
} from "@/lib/world-cup-bracket/types";

type SnapshotKnockoutMatch =
  Snapshot["knockout_predictions"]["rounds"]["round_of_16"][number];

const TEAM_CODES: Record<string, string> = {
  Argentina: "ARG",
  Australia: "AUS",
  Austria: "AUT",
  Belgium: "BEL",
  Bolivia: "BOL",
  Brazil: "BRA",
  "Burkina Faso": "BFA",
  Cameroon: "CMR",
  Canada: "CAN",
  Colombia: "COL",
  "Costa Rica": "CRC",
  Croatia: "CRO",
  Denmark: "DEN",
  Ecuador: "ECU",
  England: "ENG",
  France: "FRA",
  Germany: "GER",
  Ghana: "GHA",
  Greece: "GRE",
  Iran: "IRN",
  Italy: "ITA",
  Jamaica: "JAM",
  Japan: "JPN",
  Mexico: "MEX",
  Morocco: "MAR",
  Netherlands: "NED",
  Nigeria: "NGA",
  Panama: "PAN",
  Paraguay: "PAR",
  Peru: "PER",
  Portugal: "POR",
  Qatar: "QAT",
  Senegal: "SEN",
  Serbia: "SRB",
  Spain: "ESP",
  Sweden: "SWE",
  Tunisia: "TUN",
  Uruguay: "URU",
  USA: "USA",
  Wales: "WAL",
  Zambia: "ZAM",
};

function teamId(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function teamCode(name: string): string {
  return TEAM_CODES[name] ?? name.slice(0, 3).toUpperCase();
}

function makeTeam(name: string): Team {
  const code = teamCode(name);
  return {
    id: teamId(name),
    name,
    code,
    flag: code,
  };
}

function parseProbability(value: string | number | undefined): number {
  if (typeof value === "number") {
    return value > 1 ? value / 100 : value;
  }
  if (!value) {
    return 0;
  }
  const parsed = Number.parseFloat(value.replace("%", ""));
  if (Number.isNaN(parsed)) {
    return 0;
  }
  return parsed > 1 ? parsed / 100 : parsed;
}

function parseChampionProbability(value: string | number | undefined, simulations: number): number {
  if (typeof value === "number") {
    if (value > 1 && simulations > 0) {
      return value / simulations;
    }
    return value > 1 ? value / 100 : value;
  }
  if (!value) {
    return 0;
  }
  const match = value.match(/\(([\d.]+)%\)/);
  if (match) {
    return Number.parseFloat(match[1]) / 100;
  }
  return parseProbability(value);
}

function confidenceFromMatch(homeProbability: number, awayProbability: number): ConfidenceLevel {
  const spread = Math.abs(homeProbability - awayProbability);
  if (spread >= 0.3) return "high";
  if (spread >= 0.14) return "medium";
  return "low";
}

function parseScore(score: string | undefined, index: 0 | 1): number | undefined {
  if (!score) return undefined;
  const parts = score.split("-").map((part) => Number.parseInt(part.trim(), 10));
  return Number.isFinite(parts[index]) ? parts[index] : undefined;
}

function buildDetail(params: {
  id: string;
  home: BracketTeamSlot;
  away: BracketTeamSlot;
  reasoning: string;
  snapshotTime: string;
}): MatchDetail {
  const { id, home, away, reasoning, snapshotTime } = params;
  const homeEdge = Math.max(0.08, Math.min(0.92, home.probability));
  const awayEdge = Math.max(0.08, Math.min(0.92, away.probability));

  return {
    confidence: confidenceFromMatch(home.probability, away.probability),
    reasoningFactors: [
      {
        id: `${id}-model`,
        type: "form",
        label: "Model edge",
        description: reasoning || `${home.team.name} has the stronger projected win probability.`,
        weight: Math.max(homeEdge, awayEdge),
      },
      {
        id: `${id}-spread`,
        type: "tactical",
        label: "Probability spread",
        description: `The current snapshot gives ${home.team.name} ${Math.round(
          home.probability * 100
        )}% and ${away.team.name} ${Math.round(away.probability * 100)}%.`,
        weight: Math.min(0.9, Math.abs(homeEdge - awayEdge) + 0.35),
      },
      {
        id: `${id}-simulation`,
        type: "transition",
        label: "Simulation path",
        description: "Projected from the latest Agent snapshot and knockout simulation output.",
        weight: 0.62,
      },
    ],
    metricComparison: [
      {
        metric: "recent_form",
        label: "Win prob",
        homeValue: Math.round(home.probability * 100),
        awayValue: Math.round(away.probability * 100),
        unit: "%",
      },
      {
        metric: "xg",
        label: "Score",
        homeValue: home.score ?? 0,
        awayValue: away.score ?? 0,
        unit: "goals",
      },
      {
        metric: "pressing",
        label: "Control",
        homeValue: Math.round(45 + home.probability * 45),
        awayValue: Math.round(45 + away.probability * 45),
        unit: "idx",
      },
    ],
    dataSources: [
      { label: "Agent snapshot", href: "/data/snapshots/latest.json" },
      { label: "Prediction data", href: "/data" },
    ],
    agentTimestamp: snapshotTime,
  };
}

function makeSlot(teamName: string, probability: number, sourceSeed: string, score?: number): BracketTeamSlot {
  return {
    team: makeTeam(teamName),
    probability,
    sourceSeed,
    score,
  };
}

function convertStanding(
  row: Snapshot["group_predictions"][string]["standings"][number],
  rank: number,
  qualifiers: string[],
  bestThirdTeams: Set<string>
): GroupStanding {
  const qualifiedAs =
    qualifiers[0] === row.team
      ? "winner"
      : qualifiers[1] === row.team
        ? "runner_up"
        : bestThirdTeams.has(row.team)
          ? "best_third"
          : undefined;

  return {
    team: makeTeam(row.team),
    played: row.played,
    won: row.won,
    drawn: row.drawn,
    lost: row.lost,
    goalsFor: row.goals_for,
    goalsAgainst: row.goals_against,
    goalDiff: row.goal_diff,
    points: row.points,
    rank,
    qualifiedAs,
  };
}

function getBestThirdTeamNames(snapshot: Snapshot): Set<string> {
  const thirdRows = Object.values(snapshot.group_predictions)
    .map((group) => group.standings[2])
    .filter(Boolean)
    .sort((a, b) => {
      if (b.points !== a.points) return b.points - a.points;
      if (b.goal_diff !== a.goal_diff) return b.goal_diff - a.goal_diff;
      return b.goals_for - a.goals_for;
    })
    .slice(0, 8)
    .map((row) => row.team);

  return new Set(thirdRows);
}

function convertGroups(snapshot: Snapshot, bestThirdTeams: Set<string>): GroupStageGroup[] {
  return Object.entries(snapshot.group_predictions).map(([letter, group]) => ({
    id: letter,
    name: `Group ${letter}`,
    standings: group.standings.map((row, index) =>
      convertStanding(row, index + 1, group.qualifiers, bestThirdTeams)
    ),
  }));
}

function convertKnockoutMatch(
  match: SnapshotKnockoutMatch,
  stage: BracketMatch["stage"],
  title: string,
  snapshotTime: string
): BracketMatch {
  const homeProbability = parseProbability(match.home_win_prob);
  const awayProbability = parseProbability(match.away_win_prob);
  const home = makeSlot(
    match.home_team,
    homeProbability,
    "Projected",
    parseScore(match.predicted_score, 0)
  );
  const away = makeSlot(
    match.away_team,
    awayProbability,
    "Projected",
    parseScore(match.predicted_score, 1)
  );
  const winnerName = match.winner ?? (homeProbability >= awayProbability ? match.home_team : match.away_team);
  const loserName = match.loser ?? (winnerName === match.home_team ? match.away_team : match.home_team);

  return {
    id: match.id,
    stage,
    label: title,
    status: "upcoming",
    kickoffLabel: "Projected",
    home,
    away,
    predictedScore: match.predicted_score,
    winnerTeamId: teamId(winnerName),
    advancementRule: `${winnerName} advances over ${loserName}.`,
    detail: buildDetail({
      id: match.id,
      home,
      away,
      reasoning: match.reasoning,
      snapshotTime,
    }),
  };
}

function convertRounds(snapshot: Snapshot): BracketRound[] {
  const rounds = snapshot.knockout_predictions.rounds;
  return [
    {
      id: "round_of_16",
      title: "Round of 16",
      matches: rounds.round_of_16.map((match) =>
        convertKnockoutMatch(match, "round_of_16", "Round of 16", snapshot.snapshot_time)
      ),
    },
    {
      id: "quarter_final",
      title: "Quarter-finals",
      matches: rounds.quarter_finals.map((match) =>
        convertKnockoutMatch(match, "quarter_final", "Quarter-final", snapshot.snapshot_time)
      ),
    },
    {
      id: "semi_final",
      title: "Semi-finals",
      matches: rounds.semi_finals.map((match) =>
        convertKnockoutMatch(match, "semi_final", "Semi-final", snapshot.snapshot_time)
      ),
    },
    {
      id: "third_place",
      title: "Third place",
      matches: [
        convertKnockoutMatch(rounds.third_place, "third_place", "Third place", snapshot.snapshot_time),
      ],
    },
    {
      id: "final",
      title: "Final",
      matches: [convertKnockoutMatch(rounds.final, "final", "World Cup Final", snapshot.snapshot_time)],
    },
  ];
}

function convertTitleContenders(snapshot: Snapshot): TitleContender[] {
  const rawProbabilities =
    snapshot.knockout_predictions.champion_probabilities ??
    snapshot.champion_probabilities ??
    {};
  const contenders = Object.entries(rawProbabilities).map(([teamName, value]) => ({
    team: makeTeam(teamName),
    probability: Math.max(
      0,
      Math.min(1, parseChampionProbability(value, snapshot.monte_carlo_simulations))
    ),
  }));

  if (!contenders.some((entry) => entry.team.name === snapshot.champion)) {
    contenders.push({
      team: makeTeam(snapshot.champion),
      probability: snapshot.champion_probability,
    });
  }

  return contenders.sort((a, b) => b.probability - a.probability).slice(0, 5);
}

export function snapshotToWorldCupBracketData(snapshot: Snapshot): WorldCupBracketData {
  const bestThirdTeamNames = getBestThirdTeamNames(snapshot);
  const groups = convertGroups(snapshot, bestThirdTeamNames);
  const bestThirdTeams = groups
    .flatMap((group) => group.standings)
    .filter((row) => row.qualifiedAs === "best_third");

  return {
    title: "2026 World Cup Champion Prediction Agent",
    generatedAt: snapshot.snapshot_time,
    titleContenders: convertTitleContenders(snapshot),
    groups,
    bestThirdTeams,
    qualificationRules: [
      { slot: "1st", description: "All 12 group winners qualify directly." },
      { slot: "2nd", description: "All 12 group runners-up qualify directly." },
      { slot: "3rd", description: "The 8 best third-place teams complete the knockout field." },
    ],
    rounds: convertRounds(snapshot),
  };
}
