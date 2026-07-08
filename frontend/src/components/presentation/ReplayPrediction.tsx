/**
 * ReplayPrediction Component (Presentation Layer)
 * Replay animation player with controls
 * @TODO: Implement full UI in TP-2
 */

import type { ReplayControlsViewModel, ReplaySegmentViewModel } from "@/lib/tournament/types";

export interface ReplayPredictionProps {
  controls: ReplayControlsViewModel;
  segments: ReplaySegmentViewModel[];
}

export function ReplayPrediction({ controls, segments }: ReplayPredictionProps) {
  // TODO: Implement full UI in TP-2
  return (
    <div data-component="ReplayPrediction" className="bg-surface rounded-lg p-4">
      <div className="flex items-center gap-4 mb-4">
        <button
          onClick={controls.isPlaying ? controls.pause : controls.play}
          className="w-12 h-12 rounded-full bg-accent text-bg flex items-center justify-center"
          aria-label={controls.isPlaying ? "Pause" : "Play"}
        >
          {controls.isPlaying ? "⏸" : "▶"}
        </button>

        <button
          onClick={controls.restart}
          className="text-muted hover:text-text"
          aria-label="Restart"
        >
          ↺
        </button>

        <div className="flex-1">
          <div className="h-2 bg-surface2 rounded-full overflow-hidden">
            <div
              className="h-full bg-accent transition-all"
              style={{ width: `${controls.progress * 100}%` }}
            />
          </div>
        </div>

        <span className="text-muted text-sm">
          {controls.currentTimeDisplay} / {controls.durationDisplay}
        </span>

        <div className="flex gap-1">
          {([0.5, 1, 2] as const).map((rate) => (
            <button
              key={rate}
              onClick={() => controls.setPlaybackRate(rate)}
              className={`px-2 py-1 text-xs rounded ${
                controls.playbackRate === rate
                  ? "bg-accent text-bg"
                  : "bg-surface2 text-muted hover:text-text"
              }`}
            >
              {rate}×
            </button>
          ))}
        </div>
      </div>

      {/* Timeline segments */}
      <div className="flex justify-between text-xs text-muted">
        {segments.map((seg) => (
          <span key={seg.stage}>{seg.stageLabel}</span>
        ))}
      </div>
    </div>
  );
}
