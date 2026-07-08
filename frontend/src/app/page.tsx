import { PredictionDashboard } from "@/components/dashboard/PredictionDashboard";
import { loadSnapshotSync } from "@/lib/tournament/loader/snapshot.loader";
import { snapshotToWorldCupBracketData } from "@/lib/world-cup-bracket/snapshot-to-bracket";

export default function HomePage() {
  const snapshot = loadSnapshotSync();
  const data = snapshotToWorldCupBracketData(snapshot);

  return <PredictionDashboard data={data} />;
}
