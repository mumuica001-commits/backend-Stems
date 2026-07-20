"use client";

import { motion } from "framer-motion";
import { SpectralBars } from "@/components/ui/spectral-bars";
import { GlassPanel } from "@/components/ui/glass-panel";
import type { JobStatus } from "@/lib/types";

const STAGE_LABELS: Record<JobStatus, string> = {
  queued: "Na fila",
  analyzing: "Analisando BPM, tonalidade e acordes",
  separating: "Separando stems",
  post_processing: "Finalizando",
  completed: "Concluído",
  failed: "Falhou",
};

interface ProgressPanelProps {
  status: JobStatus | null;
  percent: number;
  message: string;
}

export function ProgressPanel({ status, percent, message }: ProgressPanelProps) {
  return (
    <GlassPanel className="flex flex-col items-center gap-6 px-8 py-12">
      <SpectralBars barCount={56} active={status !== "completed" && status !== "failed"} progress={percent} />

      <div className="w-full max-w-md text-center">
        <p className="font-display text-xl text-slate-50">
          {status ? STAGE_LABELS[status] : "Conectando..."}
        </p>
        <p className="mt-1 min-h-[1.25rem] font-body text-sm text-slate-500">{message}</p>

        <div className="mt-6 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
          <motion.div
            className="h-full bg-spectral-gradient"
            initial={{ width: 0 }}
            animate={{ width: `${percent}%` }}
            transition={{ ease: "easeOut", duration: 0.4 }}
          />
        </div>
        <p className="mt-2 font-mono text-xs text-slate-500">{Math.round(percent)}%</p>
      </div>
    </GlassPanel>
  );
}
