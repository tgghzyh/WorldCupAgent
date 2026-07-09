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
type SnapshotGroupMatch = Snapshot["group_predictions"][string]["matches"][number];
type SnapshotAnyMatch = SnapshotKnockoutMatch | SnapshotGroupMatch;

const TEAM_CODES: Record<string, string> = {
  Argentina: "ARG",
  "阿根廷": "ARG",
  "阿尔及利亚": "ALG",
  Australia: "AUS",
  "澳大利亚": "AUS",
  Austria: "AUT",
  "奥地利": "AUT",
  Belgium: "BEL",
  "比利时": "BEL",
  Bolivia: "BOL",
  "波黑": "BIH",
  Brazil: "BRA",
  "巴西": "BRA",
  "Burkina Faso": "BFA",
  "加拿大": "CAN",
  Cameroon: "CMR",
  Canada: "CAN",
  Colombia: "COL",
  "哥伦比亚": "COL",
  "Costa Rica": "CRC",
  Croatia: "CRO",
  "克罗地亚": "CRO",
  "捷克": "CZE",
  Denmark: "DEN",
  "民主刚果": "COD",
  Ecuador: "ECU",
  "厄瓜多尔": "ECU",
  "埃及": "EGY",
  England: "ENG",
  "英格兰": "ENG",
  France: "FRA",
  "法国": "FRA",
  Germany: "GER",
  "德国": "GER",
  Ghana: "GHA",
  "加纳": "GHA",
  Greece: "GRE",
  "海地": "HAI",
  Iran: "IRN",
  "伊朗": "IRN",
  "伊拉克": "IRQ",
  Italy: "ITA",
  Jamaica: "JAM",
  Japan: "JPN",
  "日本": "JPN",
  "约旦": "JOR",
  "韩国": "KOR",
  Mexico: "MEX",
  "墨西哥": "MEX",
  Morocco: "MAR",
  "摩洛哥": "MAR",
  Netherlands: "NED",
  "荷兰": "NED",
  "新西兰": "NZL",
  Nigeria: "NGA",
  "挪威": "NOR",
  Panama: "PAN",
  "巴拿马": "PAN",
  Paraguay: "PAR",
  "巴拉圭": "PAR",
  Peru: "PER",
  Portugal: "POR",
  "葡萄牙": "POR",
  Qatar: "QAT",
  "卡塔尔": "QAT",
  "沙特阿拉伯": "KSA",
  "苏格兰": "SCO",
  Senegal: "SEN",
  "塞内加尔": "SEN",
  Serbia: "SRB",
  "南非": "RSA",
  Spain: "ESP",
  "西班牙": "ESP",
  Sweden: "SWE",
  "瑞典": "SWE",
  "瑞士": "SUI",
  Tunisia: "TUN",
  "突尼斯": "TUN",
  "土耳其": "TUR",
  "乌拉圭": "URU",
  Uruguay: "URU",
  USA: "USA",
  "美国": "USA",
  "乌兹别克斯坦": "UZB",
  Wales: "WAL",
  Zambia: "ZAM",
  "佛得角": "CPV",
  "科特迪瓦": "CIV",
  "库拉索": "CUW",
};

function teamId(name: string): string {
  const normalizedName = name.trim();
  const asciiId = normalizedName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  if (asciiId) {
    return asciiId;
  }

  const unicodeId = Array.from(normalizedName)
    .map((char) => char.codePointAt(0)?.toString(16))
    .filter(Boolean)
    .join("-");
  return unicodeId ? `team-${unicodeId}` : "team-unknown";
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

function confidenceFromRaw(
  rawConfidence: string | undefined,
  homeProbability: number,
  awayProbability: number
): ConfidenceLevel {
  const normalized = rawConfidence?.toLowerCase();
  if (normalized === "high") return "high";
  if (normalized === "medium") return "medium";
  if (normalized === "low") return "low";
  return confidenceFromMatch(homeProbability, awayProbability);
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
  rawMatch?: SnapshotAnyMatch;
}): MatchDetail {
  const { id, home, away, reasoning, snapshotTime, rawMatch } = params;
  const homeEdge = Math.max(0.08, Math.min(0.92, home.probability));
  const awayEdge = Math.max(0.08, Math.min(0.92, away.probability));
  const llmFactors = rawMatch?.llm_reasoning_factors?.map((factor, index) => ({
    id: factor.id ?? `${id}-llm-${index}`,
    type: factor.type,
    label: factor.label,
    description: factor.description,
    weight: Math.max(0.05, Math.min(0.95, factor.weight)),
  }));

  return {
    confidence: confidenceFromRaw(rawMatch?.confidence, home.probability, away.probability),
    summary: reasoning || `${home.team.name} vs ${away.team.name} projected from the latest Agent snapshot.`,
    reasoningFactors: llmFactors?.length ? llmFactors : [
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
      ...(rawMatch?.llm_provider ? [{ label: `LLM: ${rawMatch.llm_provider}`, href: "/agent" }] : []),
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
    matches: group.matches.map((match) =>
      convertGroupMatch(match, "group", `Group ${letter}`, snapshot.snapshot_time)
    ),
  }));
}

function convertGroupMatch(
  match: SnapshotGroupMatch,
  stage: BracketMatch["stage"],
  title: string,
  snapshotTime: string
): BracketMatch {
  const homeProbability = parseProbability(match.home_win_prob);
  const awayProbability = parseProbability(match.away_win_prob);
  const home = makeSlot(
    match.home_team,
    homeProbability,
    "LLM projection",
    parseScore(match.predicted_score, 0)
  );
  const away = makeSlot(
    match.away_team,
    awayProbability,
    "LLM projection",
    parseScore(match.predicted_score, 1)
  );
  const winnerName =
    match.winner && match.winner !== "Draw"
      ? match.winner
      : home.score === away.score
        ? ""
        : (home.score ?? 0) > (away.score ?? 0)
          ? match.home_team
          : match.away_team;

  return {
    id: match.id,
    stage,
    label: `${title} / Match ${match.round_number}`,
    status: "upcoming",
    kickoffLabel: "Projected",
    home,
    away,
    predictedScore: match.predicted_score,
    winnerTeamId: winnerName ? teamId(winnerName) : undefined,
    advancementRule: winnerName
      ? `${winnerName} takes the group-stage edge.`
      : "Projected draw; table impact comes from goal difference.",
    detail: buildDetail({
      id: match.id,
      home,
      away,
      reasoning: match.reasoning,
      snapshotTime,
      rawMatch: match,
    }),
  };
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
      rawMatch: match,
    }),
  };
}

function convertRounds(snapshot: Snapshot): BracketRound[] {
  const rounds = snapshot.knockout_predictions.rounds;
  return [
    ...(rounds.round_of_32
      ? [
          {
            id: "round_of_32" as const,
            title: "Round of 32",
            matches: rounds.round_of_32.map((match) =>
              convertKnockoutMatch(match, "round_of_32", "Round of 32", snapshot.snapshot_time)
            ),
          },
        ]
      : []),
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
