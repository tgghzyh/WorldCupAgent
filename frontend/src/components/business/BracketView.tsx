/**
 * BracketView Component (Business Layer)
 * Consumes BracketViewModel
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { BracketNode } from "./BracketNode";
import type { BracketViewModel } from "@/lib/tournament/types";

export interface BracketViewProps {
  vm: BracketViewModel;
}

interface RoundColumnProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

function RoundColumn({ title, children, className = "" }: RoundColumnProps) {
  return (
    <div className={`flex flex-col ${className}`}>
      <div className="text-center text-xs text-muted mb-3 uppercase tracking-wider">
        {title}
      </div>
      <div className="flex-1 flex flex-col justify-around">{children}</div>
    </div>
  );
}

interface MatchPairProps {
  top: React.ReactNode;
  bottom: React.ReactNode;
}

function MatchPair({ top, bottom }: MatchPairProps) {
  return (
    <div className="flex flex-col gap-4 relative">
      {/* Connector line top */}
      <div className="absolute right-0 top-1/2 w-4 h-px bg-border -translate-y-1/2" />
      {/* Vertical connector */}
      <div className="absolute right-0 top-0 bottom-0 w-px bg-border" style={{ height: "calc(100% + 1rem)" }} />
      {top}
      {bottom}
    </div>
  );
}

export function BracketView({ vm }: BracketViewProps): JSX.Element {
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null);

  const handleExpand = (matchId: string) => {
    setExpandedMatchId(expandedMatchId === matchId ? null : matchId);
  };

  return (
    <motion.div
      className="w-full overflow-x-auto pb-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="min-w-[1000px] flex gap-8 px-4">
        {/* Round of 16 */}
        <RoundColumn title="1/8决赛" className="gap-8">
          <div className="flex flex-col gap-16">
            {vm.roundOf16.slice(0, 4).map((node, i) => (
              <MatchPair
                key={node.nodeId}
                top={
                  <BracketNode
                    vm={{ ...node, isExpanded: expandedMatchId === node.matchId }}
                    onExpand={handleExpand}
                  />
                }
                bottom={
                  vm.roundOf16[i + 4] ? (
                    <BracketNode
                      vm={{
                        ...vm.roundOf16[i + 4],
                        isExpanded: expandedMatchId === vm.roundOf16[i + 4].matchId,
                      }}
                      onExpand={handleExpand}
                    />
                  ) : (
                    <div className="h-[72px]" />
                  )
                }
              />
            ))}
          </div>
        </RoundColumn>

        {/* Quarter Finals */}
        <RoundColumn title="1/4决赛" className="gap-8">
          <div className="flex flex-col gap-32">
            {vm.quarterFinals.slice(0, 2).map((node, i) => (
              <MatchPair
                key={node.nodeId}
                top={
                  <BracketNode
                    vm={{ ...node, isExpanded: expandedMatchId === node.matchId }}
                    onExpand={handleExpand}
                  />
                }
                bottom={
                  vm.quarterFinals[i + 2] ? (
                    <BracketNode
                      vm={{
                        ...vm.quarterFinals[i + 2],
                        isExpanded: expandedMatchId === vm.quarterFinals[i + 2].matchId,
                      }}
                      onExpand={handleExpand}
                    />
                  ) : (
                    <div className="h-[72px]" />
                  )
                }
              />
            ))}
          </div>
        </RoundColumn>

        {/* Semi Finals */}
        <RoundColumn title="半决赛" className="gap-8">
          <div className="flex flex-col gap-64">
            {vm.semiFinals.slice(0, 1).map((node, i) => (
              <MatchPair
                key={node.nodeId}
                top={
                  <BracketNode
                    vm={{ ...node, isExpanded: expandedMatchId === node.matchId }}
                    onExpand={handleExpand}
                  />
                }
                bottom={
                  vm.semiFinals[i + 1] ? (
                    <BracketNode
                      vm={{
                        ...vm.semiFinals[i + 1],
                        isExpanded: expandedMatchId === vm.semiFinals[i + 1].matchId,
                      }}
                      onExpand={handleExpand}
                    />
                  ) : (
                    <div className="h-[72px]" />
                  )
                }
              />
            ))}
          </div>
        </RoundColumn>

        {/* Final + Third Place */}
        <RoundColumn title="决赛" className="gap-8">
          <div className="flex flex-col gap-16">
            {/* Final */}
            <BracketNode
              vm={{ ...vm.final, isExpanded: expandedMatchId === vm.final.matchId }}
              onExpand={handleExpand}
              isHighlighted
            />
            {/* Third Place */}
            <div className="border-t border-dashed border-border pt-4">
              <div className="text-center text-xs text-muted mb-2">三四名</div>
              <BracketNode
                vm={{
                  ...vm.thirdPlace,
                  isExpanded: expandedMatchId === vm.thirdPlace.matchId,
                }}
                onExpand={handleExpand}
              />
            </div>
          </div>
        </RoundColumn>
      </div>
    </motion.div>
  );
}
