/**
 * BracketNode Component (Business Layer)
 * Consumes BracketNodeViewModel
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Trophy } from "lucide-react";
import type { BracketNodeViewModel } from "@/lib/tournament/types";
import { ConfidenceBadge } from "@/components/ui/confidence-badge";

export interface BracketNodeProps {
  vm: BracketNodeViewModel;
  onExpand?: (matchId: string) => void;
  isHighlighted?: boolean;
}

export function BracketNode({
  vm,
  onExpand,
  isHighlighted = false,
}: BracketNodeProps): JSX.Element {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleClick = () => {
    setIsExpanded(!isExpanded);
    if (onExpand && !isExpanded) {
      onExpand(vm.matchId);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleClick();
    }
  };

  const homeWinPercent = Math.round(vm.homeWinProb * 100);
  const awayWinPercent = Math.round(vm.awayWinProb * 100);
  const isHomeWinner = vm.winner === vm.homeTeam;

  return (
    <div className="relative">
      <motion.div
        data-component="BracketNode"
        data-node-id={vm.nodeId}
        data-stage={vm.stage}
        tabIndex={0}
        role="button"
        aria-expanded={isExpanded}
        aria-label={`${vm.homeTeam} vs ${vm.awayTeam} - ${vm.stageLabel}`}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        className={`
          relative bg-surface border rounded-lg p-3 cursor-pointer
          transition-all duration-200 select-none
          hover:border-accent hover:shadow-lg
          focus:outline-none focus-visible:ring-2 focus-visible:ring-accent
          ${isHighlighted ? "border-gold shadow-[0_0_20px_rgba(234,179,8,0.3)]" : "border-border"}
        `}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        {/* Champion highlight */}
        {isHighlighted && (
          <div className="absolute -top-2 -right-2">
            <Trophy className="w-5 h-5 text-gold" />
          </div>
        )}

        {/* Home Team Row */}
        <div
          className={`
            flex items-center justify-between px-2 py-1.5 rounded
            ${isHomeWinner ? "bg-green/10" : ""}
          `}
        >
          <div className="flex items-center gap-2">
            {isHomeWinner && (
              <span className="w-2 h-2 rounded-full bg-green" />
            )}
            <span
              className={`
                font-medium text-sm
                ${isHomeWinner ? "text-green" : "text-text"}
              `}
            >
              {vm.homeTeam}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`
                text-xs font-mono
                ${isHomeWinner ? "text-green" : "text-muted"}
              `}
            >
              {homeWinPercent}%
            </span>
            {/* Mini probability bar */}
            <div className="w-12 h-1.5 bg-surface2 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-accent"
                initial={{ width: 0 }}
                animate={{ width: `${homeWinPercent}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
          </div>
        </div>

        {/* Away Team Row */}
        <div
          className={`
            flex items-center justify-between px-2 py-1.5 rounded
            ${!isHomeWinner && vm.winner === vm.awayTeam ? "bg-green/10" : ""}
          `}
        >
          <div className="flex items-center gap-2">
            {!isHomeWinner && vm.winner === vm.awayTeam && (
              <span className="w-2 h-2 rounded-full bg-green" />
            )}
            <span
              className={`
                font-medium text-sm
                ${vm.winner === vm.awayTeam ? "text-green" : "text-text"}
              `}
            >
              {vm.awayTeam}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`
                text-xs font-mono
                ${vm.winner === vm.awayTeam ? "text-green" : "text-muted"}
              `}
            >
              {awayWinPercent}%
            </span>
            <div className="w-12 h-1.5 bg-surface2 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-accent"
                initial={{ width: 0 }}
                animate={{ width: `${awayWinPercent}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
          </div>
        </div>

        {/* Expand indicator */}
        <div className="flex justify-center mt-1">
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="w-4 h-4 text-muted" />
          </motion.div>
        </div>
      </motion.div>

      {/* Expanded details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-2 p-3 bg-surface border border-border rounded-lg">
              {/* Stage label */}
              <div className="text-xs text-muted mb-2">{vm.stageLabel}</div>

              {/* Predicted score */}
              <div className="text-sm mb-3">
                <span className="text-muted">预测比分: </span>
                <span className="font-mono text-accent">{vm.predictedScore}</span>
              </div>

              {/* Reasoning preview */}
              <div className="text-xs text-muted border-t border-border pt-2">
                <p className="line-clamp-2">{vm.reasoning.text}</p>
              </div>

              {/* Confidence badge */}
              <div className="mt-2">
                <ConfidenceBadge
                  level={
                    homeWinPercent >= 70 || awayWinPercent >= 70
                      ? "High"
                      : homeWinPercent >= 50 || awayWinPercent >= 50
                      ? "Medium"
                      : "Low"
                  }
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
