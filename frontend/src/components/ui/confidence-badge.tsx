/**
 * Confidence Badge Component
 */

import type { ConfidenceLevel } from "@/lib/tournament/types";

interface ConfidenceBadgeProps {
  level: ConfidenceLevel;
  size?: "sm" | "md";
}

const levelConfig = {
  High: {
    label: "高置信",
    bgColor: "bg-green/20",
    textColor: "text-green",
    dotColor: "bg-green",
  },
  Medium: {
    label: "中置信",
    bgColor: "bg-yellow/20",
    textColor: "text-yellow",
    dotColor: "bg-yellow",
  },
  Low: {
    label: "低置信",
    bgColor: "bg-red/20",
    textColor: "text-red",
    dotColor: "bg-red",
  },
};

export function ConfidenceBadge({
  level,
  size = "sm",
}: ConfidenceBadgeProps) {
  const config = levelConfig[level];

  return (
    <div
      className={`
        inline-flex items-center gap-1.5 rounded-full
        ${config.bgColor} ${config.textColor}
        ${size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm"}
      `}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor}`} />
      <span className="font-medium">{config.label}</span>
    </div>
  );
}
