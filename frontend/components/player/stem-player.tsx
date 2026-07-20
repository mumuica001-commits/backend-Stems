"use client";

import { useCallback, useEffect } from "react";
import { GlassPanel } from "@/components/ui/glass-panel";
import { StemChannelStrip } from "./stem-channel-strip";
import { TransportBar } from "./transport-bar";
import { useStemAudioEngine } from "@/hooks/useStemAudioEngine";
import { usePlayerStore } from "@/store/playerStore";
import { stemDownloadUrl } from "@/lib/api";
import type { StemResponse } from "@/lib/types";

export function StemPlayer({ stems }: { stems: StemResponse[] }) {
  const { registerStem, play, pause, seek, trackTime } = useStemAudioEngine();
  const isPlaying = usePlayerStore((s) => s.isPlaying);
  const setCurrentTime = usePlayerStore((s) => s.setCurrentTime);

  useEffect(() => {
    const unsubscribe = trackTime((time) => setCurrentTime(time));
    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAudioReady = useCallback(
    (kind: string, el: HTMLAudioElement) => {
      registerStem(kind, el);
    },
    [registerStem]
  );

  const handlePlayPause = useCallback(() => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }, [isPlaying, play, pause]);

  return (
    <GlassPanel className="flex flex-col gap-4 p-5">
      <TransportBar onPlayPause={handlePlayPause} onSeek={seek} />

      <div className="flex flex-col gap-2">
        {stems.map((stem) => (
          <StemChannelStrip
            key={stem.kind}
            kind={stem.kind}
            confidence={stem.confidence}
            downloadUrl={stem.download_url}
            audioSrc={stemDownloadUrl(stem.download_url)}
            onAudioReady={handleAudioReady}
          />
        ))}
      </div>

      <p className="px-1 font-body text-xs text-slate-600">
        Dica: ative solo em um ou mais stems para ouvi-los isoladamente. Mute silencia
        independentemente do solo.
      </p>
    </GlassPanel>
  );
}
