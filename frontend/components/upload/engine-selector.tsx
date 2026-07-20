"use client";

import { Cpu, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EngineId, EngineInfo } from "@/lib/types";

const ENGINE_DESCRIPTIONS: Record<EngineId, string> = {
  htdemucs_6s: "6 stems — vocal, bateria, baixo, guitarra, piano, outros. Recomendado.",
  htdemucs_ft: "4 stems, fine-tuned — maior qualidade em vocal e baixo.",
  mdx_net_karaoke_2: "Especializado em separar vocal de instrumental.",
  mdx23c: "Especializado em isolar grave (baixo).",
  dev_dsp_mock: "⚠️ Teste sem IA (DSP clássico) — só para validar o app, sem baixar modelos.",
};

interface EngineSelectorProps {
  engines: EngineInfo[];
  selected: EngineId;
  onSelect: (engine: EngineId) => void;
  isLoading?: boolean;
}

export function EngineSelector({ engines, selected, onSelect, isLoading }: EngineSelectorProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-slate-400">
        <Cpu className="h-4 w-4" />
        <span className="font-body text-sm">Engine de separação</span>
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {isLoading &&
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[72px] animate-pulse rounded-xl bg-white/5" />
          ))}

        {!isLoading &&
          engines.map((engine) => {
            const isSelected = engine.id === selected;
            return (
              <button
                key={engine.id}
                onClick={() => engine.available && onSelect(engine.id)}
                disabled={!engine.available}
                className={cn(
                  "flex flex-col items-start gap-1 rounded-xl border px-4 py-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-40",
                  isSelected
                    ? "border-spectral-via bg-spectral-via/10"
                    : "border-base-border bg-base-panelSolid hover:border-slate-500"
                )}
              >
                <div className="flex w-full items-center justify-between">
                  <span className="font-mono text-xs font-semibold uppercase tracking-wide text-slate-200">
                    {engine.id}
                  </span>
                  {engine.available ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5 text-slate-600" />
                  )}
                </div>
                <span className="font-body text-xs leading-snug text-slate-500">
                  {ENGINE_DESCRIPTIONS[engine.id as EngineId]}
                </span>
              </button>
            );
          })}
      </div>
    </div>
  );
}
