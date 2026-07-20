"use client";

import { Play, Pause } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { formatDuration } from "@/lib/utils";
import { usePlayerStore } from "@/store/playerStore";

interface TransportBarProps {
  onPlayPause: () => void;
  onSeek: (time: number) => void;
}

export function TransportBar({ onPlayPause, onSeek }: TransportBarProps) {
  const isPlaying = usePlayerStore((s) => s.isPlaying);
  const currentTime = usePlayerStore((s) => s.currentTime);
  const duration = usePlayerStore((s) => s.duration);

  return (
    <div className="flex items-center gap-4 rounded-xl border border-base-border bg-base-panelSolid px-5 py-4">
      <Button variant="primary" size="icon" onClick={onPlayPause} aria-label={isPlaying ? "Pausar" : "Reproduzir"}>
        {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
      </Button>

      <span className="font-mono text-xs text-slate-400 w-10 text-right">{formatDuration(currentTime)}</span>

      <div className="flex-1">
        <Slider
          value={[currentTime]}
          max={Math.max(duration, 0.01)}
          step={0.01}
          trackColor="#DB2777"
          onValueChange={([v]) => onSeek(v)}
          aria-label="Posição de reprodução"
        />
      </div>

      <span className="font-mono text-xs text-slate-400 w-10">{formatDuration(duration)}</span>
    </div>
  );
}
