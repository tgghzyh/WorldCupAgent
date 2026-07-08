import { WorldCupBracketView } from "@/components/world-cup-bracket/WorldCupBracketView";
import { loadSnapshotSync } from "@/lib/tournament/loader/snapshot.loader";
import { snapshotToWorldCupBracketData } from "@/lib/world-cup-bracket/snapshot-to-bracket";

export default function SchedulePage() {
  const snapshot = loadSnapshotSync();
  const data = snapshotToWorldCupBracketData(snapshot);

  return <WorldCupBracketView data={data} />;
}
