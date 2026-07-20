"use client";

import { useEffect, useRef, useState } from "react";
import { jobWebSocketUrl } from "@/lib/api";
import type { JobProgressMessage, JobStatus } from "@/lib/types";

interface JobProgressState {
  status: JobStatus | null;
  percent: number;
  message: string;
  isTerminal: boolean;
}

export function useJobProgress(jobId: string | null) {
  const [progress, setProgress] = useState<JobProgressState>({
    status: null,
    percent: 0,
    message: "Conectando...",
    isTerminal: false,
  });
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);

  useEffect(() => {
    if (!jobId) return;

    let cancelled = false;
    let reconnectTimeout: ReturnType<typeof setTimeout>;

    function connect() {
      if (cancelled) return;

      const socket = new WebSocket(jobWebSocketUrl(jobId!));
      socketRef.current = socket;

      socket.onmessage = (event) => {
        const data: JobProgressMessage = JSON.parse(event.data);
        if (data.type === "heartbeat") return;

        const isTerminal = data.status === "completed" || data.status === "failed";
        setProgress({
          status: data.status ?? null,
          percent: data.percent ?? 0,
          message: data.message ?? data.error ?? "",
          isTerminal,
        });

        if (isTerminal) {
          socket.close();
        }
      };

      socket.onclose = () => {
        if (cancelled || progress.isTerminal) return;
        // reconexão com backoff simples — cobre quedas de rede momentâneas
        reconnectAttemptsRef.current += 1;
        const delay = Math.min(1000 * reconnectAttemptsRef.current, 5000);
        reconnectTimeout = setTimeout(connect, delay);
      };

      socket.onerror = () => {
        socket.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimeout);
      socketRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  return progress;
}
