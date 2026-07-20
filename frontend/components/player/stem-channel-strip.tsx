"use client";

import { useEffect, useRef } from "react";
import { Volume2, VolumeX, Headphones, Download } from "lucide-react";
import { Waveform } from "./waveform";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { usePlayerStore } from "@/store/playerStore";
import { STEM_LABELS, type StemKind } from "@/lib/types";
import { stemDownloadUrl } from "@/lib/api";

const STEM_COLORS: Record<string, string> = {
  vocals: "#FF6F5E",
  backing_vocals: "#FB923C",
  drums: "#F5A623",
  bass: "#8B5CF6",
  guitar: "#A3E635",
  piano: "#38BDF8",
  other: "#94A3B8",
};

interface StemChannelStripProps {
  kind: StemKind;
  confidence: number;
  downloadUrl: string;
  audioSrc: string;
  onAudioReady: (kind: string, el: HTMLAudioElement) => void;
}

export function StemChannelStrip({ kind, confidence, downloadUrl, audioSrc, onAudioReady }: StemChannelStripProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const color = STEM_COLORS[kind] ?? STEM_COLORS.other;

  const channel = usePlayerStore((s) => s.channels[kind]);
  const registerStem = usePlayerStore((s) => s.registerStem);
  const setVolume = usePlayerStore((s) => s.setVolume);
  const setPan = usePlayerStore((s) => s.setPan);
  const toggleMute = usePlayerStore((s) => s.toggleMute);
  const toggleSolo = usePlayerStore((s) => s.toggleSolo);

  useEffect(() => {
    registerStem(kind);
  }, [kind, registerStem]);

  useEffect(() => {
    if (audioRef.current) onAudioReady(kind, audioRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind]);

  if (!channel) return null;

  const isLowConfidence = confidence < 0.5;

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-base-border bg-base-panelSolid p-4 sm:flex-row sm:items-center">
      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <audio ref={audioRef} src={audioSrc} preload="metadata" crossOrigin="anonymous" />

      <div className="flex items-center gap-3 sm:w-40 shrink-0">
        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
        <div>
          <p className="font-body text-sm font-medium text-slate-100">{STEM_LABELS[kind]}</p>
          <p className={cn("font-mono text-[11px]", isLowConfidence ? "text-amber-400" : "text-slate-500")}>
            {Math.round(confidence * 100)}% confiança
          </p>
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <Waveform audioEl={audioRef.current} color={color} height={44} />
      </div>

      <div className="flex items-center gap-3 sm:w-64 shrink-0">
        <button
          onClick={() => toggleMute(kind)}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg border transition-colors",
            channel.muted ? "border-red-500/50 bg-red-500/10 text-red-400" : "border-base-border text-slate-400 hover:text-white"
          )}
          aria-label="Mudo"
          aria-pressed={channel.muted}
        >
          {channel.muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
        </button>

        <button
          onClick={() => toggleSolo(kind)}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg border transition-colors",
            channel.soloed ? "border-amber-400/60 bg-amber-400/10 text-amber-400" : "border-base-border text-slate-400 hover:text-white"
          )}
          aria-label="Solo"
          aria-pressed={channel.soloed}
        >
          <Headphones className="h-4 w-4" />
        </button>

        <div className="w-24">
          <Slider
            value={[channel.volume]}
            max={1}
            step={0.01}
            trackColor={color}
            onValueChange={([v]) => setVolume(kind, v)}
            aria-label={`Volume de ${STEM_LABELS[kind]}`}
          />
        </div>

        <div className="w-16">
          <Slider
            value={[channel.pan]}
            min={-1}
            max={1}
            step={0.01}
            trackColor="#64748B"
            onValueChange={([v]) => setPan(kind, v)}
            aria-label={`Pan de ${STEM_LABELS[kind]}`}
          />
        </div>

        <a href={stemDownloadUrl(downloadUrl)} download>
          <Button variant="ghost" size="icon" aria-label={`Baixar ${STEM_LABELS[kind]}`}>
            <Download className="h-4 w-4" />
          </Button>
        </a>
      </div>
    </div>
  );
}
