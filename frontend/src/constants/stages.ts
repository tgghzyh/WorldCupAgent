/**
 * Stage Definitions
 * Tournament stage constants
 */

export const KNOCKOUT_STAGES = {
  ROUND_OF_16: "round_of_16",
  QUARTER_FINALS: "quarter_finals",
  SEMI_FINALS: "semi_finals",
  THIRD_PLACE: "third_place",
  FINAL: "final",
} as const;

export const KNOCKOUT_STAGE_LABELS: Record<string, string> = {
  [KNOCKOUT_STAGES.ROUND_OF_16]: "1/8决赛",
  [KNOCKOUT_STAGES.QUARTER_FINALS]: "1/4决赛",
  [KNOCKOUT_STAGES.SEMI_FINALS]: "半决赛",
  [KNOCKOUT_STAGES.THIRD_PLACE]: "三四名决赛",
  [KNOCKOUT_STAGES.FINAL]: "决赛",
};

export const GROUP_STAGES = {
  ROUND_1: "第1轮",
  ROUND_2: "第2轮",
  ROUND_3: "第3轮",
} as const;

export const GROUP_LETTERS = [
  "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"
] as const;

export const CONFIDENCE_LEVELS = {
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
} as const;

export const CONFIDENCE_COLORS: Record<string, string> = {
  [CONFIDENCE_LEVELS.HIGH]: "green",
  [CONFIDENCE_LEVELS.MEDIUM]: "yellow",
  [CONFIDENCE_LEVELS.LOW]: "red",
};
