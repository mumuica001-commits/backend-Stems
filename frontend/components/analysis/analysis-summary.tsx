import { GlassPanel } from "@/components/ui/glass-panel";
import { Activity, Music2, Gauge, Clock } from "lucide-react";
import type { AnalysisResponse } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

function Metric({
  icon: Icon,
  label,
  value,
  confidence,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  confidence?: number;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/5">
        <Icon className="h-4 w-4 text-slate-400" />
      </div>
      <div>
        <p className="font-mono text-base leading-none text-slate-100">{value}</p>
        <p className="mt-1 font-body text-xs text-slate-500">
          {label}
          {confidence !== undefined && (
            <span className="ml-1 text-slate-600">· {Math.round(confidence * 100)}% confiança</span>
          )}
        </p>
      </div>
    </div>
  );
}

export function AnalysisSummary({ analysis }: { analysis: AnalysisResponse }) {
  return (
    <GlassPanel className="grid grid-cols-2 gap-5 p-5 sm:grid-cols-4">
      <Metric icon={Activity} label="BPM" value={analysis.bpm?.toFixed(1) ?? "—"} confidence={analysis.bpm_confidence} />
      <Metric icon={Music2} label="Tonalidade" value={analysis.key ?? "—"} confidence={analysis.key_confidence} />
      <Metric icon={Gauge} label="Loudness" value={analysis.lufs_integrated != null ? `${analysis.lufs_integrated} LUFS` : "—"} />
      <Metric
        icon={Clock}
        label={`Compasso ${analysis.time_signature ?? ""}`}
        value={analysis.duration_seconds != null ? formatDuration(analysis.duration_seconds) : "—"}
      />
    </GlassPanel>
  );
}
