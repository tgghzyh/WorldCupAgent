import { MatchNode } from "@/components/world-cup-bracket/MatchNode";
import type { BracketMatch } from "@/lib/world-cup-bracket/types";

export function BracketNode({ match }: { match: BracketMatch }) {
  return <MatchNode match={match} />;
}
