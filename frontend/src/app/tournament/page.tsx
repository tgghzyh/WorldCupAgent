/**
 * Tournament Page
 * Displays Bracket and Champion Prediction
 */

import { Suspense } from "react";
import { loadSnapshot } from "@/lib/tournament/loader/snapshot.loader";
import { BracketVMBuilder } from "@/lib/tournament/viewModels/bracket.vm";
import { BracketView } from "@/components/business/BracketView";
import { Trophy, Clock, Sparkles } from "lucide-react";

interface PageProps {
  searchParams?: Promise<{ highlight?: string }>;
}

export default async function TournamentPage({ searchParams }: PageProps) {
  const snapshot = await loadSnapshot();
  const bracketVm = BracketVMBuilder.build(snapshot);

  const champion = snapshot.champion;
  const probability = snapshot.champion_probability;

  // Parse searchParams safely
  let highlightTeam: string | null = null;
  try {
    const params = await searchParams;
    highlightTeam = params?.highlight || null;
  } catch {
    // ignore
  }

  return (
    <main className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-border bg-surface/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-text flex items-center gap-2">
                <Trophy className="w-6 h-6 text-gold" />
                Tournament Bracket
              </h1>
              <p className="text-sm text-muted mt-1">
                世界杯预测 · 淘汰赛对阵图
              </p>
            </div>

            {/* Champion prediction banner */}
            <div className="flex items-center gap-4 bg-gradient-to-r from-gold/10 to-accent/10 px-4 py-2 rounded-lg border border-gold/20">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-gold" />
                <span className="text-sm text-muted">预测冠军</span>
              </div>
              <div className="text-lg font-bold text-gold">{champion}</div>
              <div className="text-sm text-muted">
                {Math.round(probability * 100)}% 概率
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Bracket section */}
      <section className="py-8">
        <Suspense fallback={<BracketSkeleton />}>
          <BracketView vm={bracketVm} />
        </Suspense>
      </section>

      {/* Legend */}
      <footer className="border-t border-border py-4">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-center gap-6 text-xs text-muted">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green" />
              <span>预测晋级</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-gold" />
              <span>决赛</span>
            </div>
            <div className="flex items-center gap-2">
              <Trophy className="w-3 h-3 text-gold" />
              <span>点击展开详情</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-3 h-3" />
              <span>数据来源: AI Agent</span>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}

function BracketSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4">
      <div className="flex gap-8 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex flex-col gap-4">
            <div className="h-4 w-16 mx-auto bg-surface2 rounded" />
            {[1, 2, 4, 8][i - 1] > 0 &&
              Array.from({ length: [1, 2, 4, 8][i - 1] }).map((_, j) => (
                <div
                  key={j}
                  className="h-20 w-40 bg-surface rounded-lg"
                />
              ))}
          </div>
        ))}
      </div>
    </div>
  );
}
