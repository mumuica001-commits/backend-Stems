"use client";

import { useEffect, useRef } from "react";
import WaveSurfer from "wavesurfer.js";

interface WaveformProps {
  audioEl: HTMLAudioElement | null;
  color: string;
  height?: number;
}

/**
 * Importante: passamos `media: audioEl` para o WaveSurfer, o que faz ele
 * SÓ desenhar a waveform e NÃO criar seu próprio pipeline de playback.
 * O playback real (play/pause/volume/pan) é todo controlado pelo
 * useStemAudioEngine via Web Audio API — WaveSurfer aqui é puramente visual.
 */
export function Waveform({ audioEl, color, height = 56 }: WaveformProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);

  useEffect(() => {
    if (!containerRef.current || !audioEl) return;

    const wavesurfer = WaveSurfer.create({
      container: containerRef.current,
      media: audioEl,
      waveColor: `${color}55`,
      progressColor: color,
      cursorColor: "#ffffff88",
      height,
      barWidth: 2,
      barGap: 2,
      barRadius: 2,
      interact: true,
      normalize: true,
    });

    wavesurferRef.current = wavesurfer;

    return () => {
      wavesurfer.destroy();
    };
  }, [audioEl, color, height]);

  return <div ref={containerRef} className="w-full" />;
}
