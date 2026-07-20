"use client";

import { useCallback, useEffect, useRef } from "react";
import { usePlayerStore } from "@/store/playerStore";

interface StemNodes {
  audioEl: HTMLAudioElement;
  sourceNode: MediaElementAudioSourceNode;
  gainNode: GainNode;
  panNode: StereoPannerNode;
}

/**
 * Motor de áudio: cada stem tem seu próprio <audio> (oculto), conectado a
 * um GainNode (volume) + StereoPannerNode (pan) dentro de um único
 * AudioContext compartilhado. Isso dá controle real de volume/pan por
 * canal — coisa que o atributo `.volume` de um <audio> sozinho não
 * consegue fazer (não existe pan nativo em HTMLMediaElement).
 *
 * Sincronização de transporte: play/pause/seek são disparados em todos
 * os elementos de uma vez. Para faixas de poucos minutos o drift entre
 * elementos é imperceptível; para masters muito longos, uma correção
 * periódica de currentTime seria o próximo passo (fora do escopo desta fase).
 */
export function useStemAudioEngine() {
  const contextRef = useRef<AudioContext | null>(null);
  const nodesRef = useRef<Map<string, StemNodes>>(new Map());
  const { channels, isAudible, setDuration, setPlaying, setCurrentTime } = usePlayerStore();

  const getContext = useCallback(() => {
    if (!contextRef.current) {
      contextRef.current = new AudioContext();
    }
    return contextRef.current;
  }, []);

  const registerStem = useCallback(
    (kind: string, audioEl: HTMLAudioElement) => {
      if (nodesRef.current.has(kind)) return;

      const ctx = getContext();
      const sourceNode = ctx.createMediaElementSource(audioEl);
      const gainNode = ctx.createGain();
      const panNode = ctx.createStereoPanner();

      sourceNode.connect(gainNode).connect(panNode).connect(ctx.destination);
      nodesRef.current.set(kind, { audioEl, sourceNode, gainNode, panNode });

      audioEl.addEventListener("loadedmetadata", () => {
        if (audioEl.duration && Number.isFinite(audioEl.duration)) {
          setDuration(audioEl.duration);
        }
      });
    },
    [getContext, setDuration]
  );

  // aplica volume/pan/mute/solo do store nos nós reais sempre que mudam
  useEffect(() => {
    nodesRef.current.forEach((nodes, kind) => {
      const channel = channels[kind];
      if (!channel) return;
      const audible = isAudible(kind);
      nodes.gainNode.gain.value = audible ? channel.volume : 0;
      nodes.panNode.pan.value = channel.pan;
    });
  }, [channels, isAudible]);

  const play = useCallback(async () => {
    const ctx = getContext();
    if (ctx.state === "suspended") await ctx.resume();

    const elements = Array.from(nodesRef.current.values()).map((n) => n.audioEl);
    await Promise.all(elements.map((el) => el.play().catch(() => undefined)));
    setPlaying(true);
  }, [getContext, setPlaying]);

  const pause = useCallback(() => {
    nodesRef.current.forEach((n) => n.audioEl.pause());
    setPlaying(false);
  }, [setPlaying]);

  const seek = useCallback(
    (time: number) => {
      nodesRef.current.forEach((n) => {
        n.audioEl.currentTime = time;
      });
      setCurrentTime(time);
    },
    [setCurrentTime]
  );

  const trackTime = useCallback((onTick: (time: number) => void) => {
    const first = nodesRef.current.values().next().value as StemNodes | undefined;
    if (!first) return () => undefined;

    const handler = () => onTick(first.audioEl.currentTime);
    first.audioEl.addEventListener("timeupdate", handler);
    return () => first.audioEl.removeEventListener("timeupdate", handler);
  }, []);

  useEffect(() => {
    return () => {
      contextRef.current?.close().catch(() => undefined);
    };
  }, []);

  return { registerStem, play, pause, seek, trackTime };
}
