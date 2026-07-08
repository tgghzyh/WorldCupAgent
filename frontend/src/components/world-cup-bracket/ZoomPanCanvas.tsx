"use client";

import * as React from "react";
import { Move, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n";

type ZoomPanCanvasProps = {
  children: React.ReactNode;
};

export function ZoomPanCanvas({ children }: ZoomPanCanvasProps) {
  const { t } = useI18n();
  const [scale, setScale] = React.useState(0.9);
  const [position, setPosition] = React.useState({ x: 0, y: 0 });
  const dragStart = React.useRef<{ x: number; y: number; px: number; py: number } | null>(null);

  function clampScale(next: number) {
    return Math.min(1.6, Math.max(0.55, next));
  }

  function zoomBy(delta: number) {
    setScale((current) => clampScale(current + delta));
  }

  function reset() {
    setScale(0.9);
    setPosition({ x: 0, y: 0 });
  }

  function onWheel(event: React.WheelEvent<HTMLDivElement>) {
    event.preventDefault();
    const delta = event.deltaY > 0 ? -0.06 : 0.06;
    zoomBy(delta);
  }

  function onPointerDown(event: React.PointerEvent<HTMLDivElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    dragStart.current = {
      x: event.clientX,
      y: event.clientY,
      px: position.x,
      py: position.y,
    };
  }

  function onPointerMove(event: React.PointerEvent<HTMLDivElement>) {
    if (!dragStart.current) return;
    setPosition({
      x: dragStart.current.px + event.clientX - dragStart.current.x,
      y: dragStart.current.py + event.clientY - dragStart.current.y,
    });
  }

  function onPointerUp(event: React.PointerEvent<HTMLDivElement>) {
    dragStart.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
  }

  return (
    <section className="rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.78)] shadow-[0_24px_80px_rgba(79,58,34,0.10)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[color:var(--border)] px-4 py-3">
        <div className="flex items-center gap-2 text-sm text-[color:var(--muted)]">
          <Move className="h-4 w-4" />
          {t("schedule.wheelHelp")}
        </div>
        <div className="flex items-center gap-2">
          <Button className="h-8 px-3" aria-label="Zoom out" onClick={() => zoomBy(-0.1)}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="min-w-14 text-center text-xs font-medium text-[color:var(--muted)]">
            {Math.round(scale * 100)}%
          </span>
          <Button className="h-8 px-3" aria-label="Zoom in" onClick={() => zoomBy(0.1)}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button className="h-8 px-3" aria-label="Reset view" onClick={reset}>
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <div
        className="h-[680px] touch-none cursor-grab overflow-hidden active:cursor-grabbing md:h-[760px]"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
      >
        <div
          className="origin-top-left p-5 transition-transform duration-75 md:p-8"
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
          }}
        >
          {children}
        </div>
      </div>
    </section>
  );
}
