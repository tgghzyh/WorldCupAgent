import type { Locale } from "@/i18n";

export type LocalizedText = Record<Locale, string>;

export type ScheduleMilestone = {
  title: LocalizedText;
  date: string;
  venue: string;
  location: LocalizedText;
  description: LocalizedText;
  badge: LocalizedText;
};

export type SchedulePhase = {
  title: LocalizedText;
  dateRange: LocalizedText;
  matches: number;
  description: LocalizedText;
};

export type HostCity = {
  country: LocalizedText;
  city: LocalizedText;
  venue: string;
  role: LocalizedText;
};

export type ScheduleSource = {
  label: string;
  url: string;
};

export const realWorldCupSchedule = {
  verifiedAt: "2026-07-07",
  summary: {
    teams: 48,
    matches: 104,
    hostCities: 16,
    dateRange: {
      en: "June 11 - July 19, 2026",
      zh: "2026 年 6 月 11 日至 7 月 19 日",
    },
  },
  milestones: [
    {
      title: {
        en: "Opening match",
        zh: "揭幕战",
      },
      date: "2026-06-11",
      venue: "Estadio Azteca",
      location: {
        en: "Mexico City, Mexico",
        zh: "墨西哥，墨西哥城",
      },
      badge: {
        en: "Confirmed",
        zh: "已确认",
      },
      description: {
        en: "The 2026 World Cup begins at Estadio Azteca, making Mexico City the first host city to open the tournament for a third time.",
        zh: "2026 世界杯将在阿兹特克体育场开幕，墨西哥城也将第三次承办世界杯揭幕战。",
      },
    },
    {
      title: {
        en: "Canada opener",
        zh: "加拿大首战",
      },
      date: "2026-06-12",
      venue: "BMO Field",
      location: {
        en: "Toronto, Canada",
        zh: "加拿大，多伦多",
      },
      badge: {
        en: "Host opener",
        zh: "东道主首战",
      },
      description: {
        en: "Canada starts its home tournament schedule in Toronto.",
        zh: "加拿大将在多伦多开启本届世界杯的主场赛程。",
      },
    },
    {
      title: {
        en: "United States opener",
        zh: "美国首战",
      },
      date: "2026-06-12",
      venue: "SoFi Stadium",
      location: {
        en: "Los Angeles, United States",
        zh: "美国，洛杉矶",
      },
      badge: {
        en: "Host opener",
        zh: "东道主首战",
      },
      description: {
        en: "The United States opens its campaign in Los Angeles on the second tournament day.",
        zh: "美国队将在赛事第二天于洛杉矶开启本土世界杯征程。",
      },
    },
    {
      title: {
        en: "Knockout stage begins",
        zh: "淘汰赛开始",
      },
      date: "2026-06-28",
      venue: "Multiple venues",
      location: {
        en: "Across host cities",
        zh: "多个承办城市",
      },
      badge: {
        en: "Round of 32",
        zh: "32 强",
      },
      description: {
        en: "The expanded format introduces a Round of 32 before the traditional Round of 16.",
        zh: "扩军后的赛制会先进入 32 强淘汰赛，再进入传统 16 强阶段。",
      },
    },
    {
      title: {
        en: "Final",
        zh: "决赛",
      },
      date: "2026-07-19",
      venue: "MetLife Stadium",
      location: {
        en: "New York/New Jersey, United States",
        zh: "美国，纽约/新泽西",
      },
      badge: {
        en: "Champion decided",
        zh: "冠军诞生",
      },
      description: {
        en: "The champion will be crowned at MetLife Stadium in the New York/New Jersey host region.",
        zh: "冠军将在纽约/新泽西赛区的大都会人寿体育场诞生。",
      },
    },
  ] satisfies ScheduleMilestone[],
  phases: [
    {
      title: { en: "Group stage", zh: "小组赛" },
      dateRange: { en: "June 11 - June 27", zh: "6 月 11 日 - 6 月 27 日" },
      matches: 72,
      description: {
        en: "12 groups of four teams. The top two from each group and eight best third-place teams advance.",
        zh: "12 个小组各 4 队，小组前两名和 8 支成绩最好的第三名晋级。",
      },
    },
    {
      title: { en: "Round of 32", zh: "32 强" },
      dateRange: { en: "June 28 - July 3", zh: "6 月 28 日 - 7 月 3 日" },
      matches: 16,
      description: {
        en: "First knockout round in the expanded 48-team format.",
        zh: "48 队扩军赛制下的第一轮淘汰赛。",
      },
    },
    {
      title: { en: "Round of 16", zh: "16 强" },
      dateRange: { en: "July 4 - July 7", zh: "7 月 4 日 - 7 月 7 日" },
      matches: 8,
      description: {
        en: "Eight winners progress to the quarter-finals.",
        zh: "8 支胜队晋级四分之一决赛。",
      },
    },
    {
      title: { en: "Quarter-finals", zh: "四分之一决赛" },
      dateRange: { en: "July 9 - July 11", zh: "7 月 9 日 - 7 月 11 日" },
      matches: 4,
      description: {
        en: "The final eight teams play across the host network.",
        zh: "最后 8 支球队将在不同承办城市争夺四强席位。",
      },
    },
    {
      title: { en: "Semi-finals", zh: "半决赛" },
      dateRange: { en: "July 14 - July 15", zh: "7 月 14 日 - 7 月 15 日" },
      matches: 2,
      description: {
        en: "Two matches decide the finalists.",
        zh: "两场比赛决定最终进入决赛的球队。",
      },
    },
    {
      title: { en: "Third-place match", zh: "三四名决赛" },
      dateRange: { en: "July 18", zh: "7 月 18 日" },
      matches: 1,
      description: {
        en: "The losing semi-finalists meet before the final weekend closes.",
        zh: "两支半决赛失利球队将在决赛前一天争夺季军。",
      },
    },
    {
      title: { en: "Final", zh: "决赛" },
      dateRange: { en: "July 19", zh: "7 月 19 日" },
      matches: 1,
      description: {
        en: "The tournament concludes in the New York/New Jersey host region.",
        zh: "本届赛事将在纽约/新泽西赛区收官。",
      },
    },
  ] satisfies SchedulePhase[],
  hostCities: [
    {
      country: { en: "Canada", zh: "加拿大" },
      city: { en: "Toronto", zh: "多伦多" },
      venue: "BMO Field",
      role: { en: "Canada opener", zh: "加拿大首战" },
    },
    {
      country: { en: "Canada", zh: "加拿大" },
      city: { en: "Vancouver", zh: "温哥华" },
      venue: "BC Place",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "Mexico", zh: "墨西哥" },
      city: { en: "Mexico City", zh: "墨西哥城" },
      venue: "Estadio Azteca",
      role: { en: "Opening match", zh: "揭幕战" },
    },
    {
      country: { en: "Mexico", zh: "墨西哥" },
      city: { en: "Guadalajara", zh: "瓜达拉哈拉" },
      venue: "Estadio Akron",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "Mexico", zh: "墨西哥" },
      city: { en: "Monterrey", zh: "蒙特雷" },
      venue: "Estadio BBVA",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "Atlanta", zh: "亚特兰大" },
      venue: "Mercedes-Benz Stadium",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "Boston", zh: "波士顿" },
      venue: "Gillette Stadium",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "Dallas", zh: "达拉斯" },
      venue: "AT&T Stadium",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "Houston", zh: "休斯敦" },
      venue: "NRG Stadium",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "Kansas City", zh: "堪萨斯城" },
      venue: "Arrowhead Stadium",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "Los Angeles", zh: "洛杉矶" },
      venue: "SoFi Stadium",
      role: { en: "United States opener", zh: "美国首战" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "Miami", zh: "迈阿密" },
      venue: "Hard Rock Stadium",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "New York/New Jersey", zh: "纽约/新泽西" },
      venue: "MetLife Stadium",
      role: { en: "Final", zh: "决赛" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "Philadelphia", zh: "费城" },
      venue: "Lincoln Financial Field",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "San Francisco Bay Area", zh: "旧金山湾区" },
      venue: "Levi's Stadium",
      role: { en: "Host city", zh: "承办城市" },
    },
    {
      country: { en: "United States", zh: "美国" },
      city: { en: "Seattle", zh: "西雅图" },
      venue: "Lumen Field",
      role: { en: "Host city", zh: "承办城市" },
    },
  ] satisfies HostCity[],
  sources: [
    {
      label: "FIFA official schedule announcement",
      url: "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/fifa-world-cup-26-final-to-be-held-in-new-york-new-jersey-mexico-city-to-host-historic-opening-match-as-schedule-revealed",
    },
    {
      label: "FIFA World Cup 26 tournament hub",
      url: "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
    },
    {
      label: "2026 FIFA World Cup overview",
      url: "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup",
    },
  ] satisfies ScheduleSource[],
};
