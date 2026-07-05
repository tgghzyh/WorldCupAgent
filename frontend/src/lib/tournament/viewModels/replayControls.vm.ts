/**
 * ReplayControls ViewModel
 * Builds ReplayControlsViewModel for replay animation
 */

import type { ReplayControlsViewModel, ReplaySegmentViewModel } from "@/lib/tournament/types";

export class ReplayControlsVMBuilder {
  private isPlaying: boolean = false;
  private currentTime: number = 0;
  private duration: number = 20; // seconds
  private playbackRate: 0.5 | 1 | 2 = 1;
  private intervalId: ReturnType<typeof setInterval> | null = null;

  /**
   * Build ReplayControlsViewModel
   */
  build(): ReplayControlsViewModel {
    return {
      isPlaying: this.isPlaying,
      currentTime: this.currentTime,
      duration: this.duration,
      playbackRate: this.playbackRate,
      progress: this.currentTime / this.duration,
      currentTimeDisplay: this.formatTime(this.currentTime),
      durationDisplay: this.formatTime(this.duration),
      play: () => this.play(),
      pause: () => this.pause(),
      restart: () => this.restart(),
      seek: (time: number) => this.seek(time),
      setPlaybackRate: (rate: 0.5 | 1 | 2) => this.setPlaybackRate(rate),
    };
  }

  private play(): void {
    if (this.isPlaying) return;
    this.isPlaying = true;

    this.intervalId = setInterval(() => {
      this.currentTime += 0.1 * this.playbackRate;
      if (this.currentTime >= this.duration) {
        this.currentTime = this.duration;
        this.pause();
      }
    }, 100);
  }

  private pause(): void {
    this.isPlaying = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private restart(): void {
    this.pause();
    this.currentTime = 0;
  }

  private seek(time: number): void {
    this.currentTime = Math.max(0, Math.min(time, this.duration));
  }

  private setPlaybackRate(rate: 0.5 | 1 | 2): void {
    this.playbackRate = rate;
  }

  private formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }

  /**
   * Build replay timeline segments
   */
  static buildTimeline(): ReplaySegmentViewModel[] {
    return [
      { stage: "group_stage", stageLabel: "Group Stage", startTime: 0, endTime: 4, duration: 4 },
      { stage: "round_of_16", stageLabel: "Round of 16", startTime: 4, endTime: 8, duration: 4 },
      { stage: "quarter_finals", stageLabel: "Quarter Finals", startTime: 8, endTime: 12, duration: 4 },
      { stage: "semi_finals", stageLabel: "Semi Finals", startTime: 12, endTime: 16, duration: 4 },
      { stage: "final", stageLabel: "Final", startTime: 16, endTime: 20, duration: 4 },
    ];
  }

  /**
   * Get current stage based on time
   */
  static getCurrentStage(time: number): string {
    const segments = this.buildTimeline();
    for (const segment of segments) {
      if (time >= segment.startTime && time < segment.endTime) {
        return segment.stage;
      }
    }
    return "champion";
  }

  /**
   * Cleanup
   */
  destroy(): void {
    this.pause();
  }
}
