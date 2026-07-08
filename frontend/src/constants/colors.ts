/**
 * Color Tokens
 * CSS Variables for theming
 */

export const COLORS = {
  // Background
  bg: "#0a0e14",
  surface: "#131a24",
  surface2: "#1a2333",
  border: "#1e2a3a",

  // Text
  text: "#cdd9e5",
  muted: "#768390",

  // Accent
  accent: "#58a6ff",

  // Semantic
  green: "#3fb950", // High confidence / home win
  yellow: "#d29922", // Medium confidence / draw
  red: "#f85149", // Low confidence / away win
  orange: "#e8854a", // Alternative away
  purple: "#bc8cff", // Special state
  gold: "#ffd700", // Champion
} as const;

export const COLOR_TOKENS = {
  "--bg": COLORS.bg,
  "--surface": COLORS.surface,
  "--surface2": COLORS.surface2,
  "--border": COLORS.border,
  "--text": COLORS.text,
  "--muted": COLORS.muted,
  "--accent": COLORS.accent,
  "--green": COLORS.green,
  "--yellow": COLORS.yellow,
  "--red": COLORS.red,
  "--orange": COLORS.orange,
  "--purple": COLORS.purple,
  "--gold": COLORS.gold,
} as const;
