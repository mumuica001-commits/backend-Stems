"use client";

export const dynamic = 'force-dynamic';

import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, AlertTriangle } from "lucide-react";
import { ProgressPanel } from "@/components/processing/progress-panel";
import { AnalysisSummary } from "@/components/analysis/analysis-summary";
import { StemPlayer } from "@/components/player/stem-player";
import { Button } from "@/components/ui/button";
import { useJobProgress } from "@/hooks/useJobProgress";
import { useJob } from "@/hooks/useJob";

export default function JobPage() {
  const params = useParams<{ jobId: string }>();
  const router = useRouter();
  const jobId = params.jobId;

  const progress = useJobProgress(jobId);
  const isTerminal = progress.isTerminal || progress.status === "completed";

  const { data: job, isLoading } = useJob(jobId, { enabled: isTerminal });

  return (
    <main className="mx-auto min-h-screen max-w-4xl px-6 py-16">
      <Button variant="ghost" size="sm" onClick={() => router.push("/")} className="mb-8">
        <ArrowLeft className="h-4 w-4" /> Novo upload
      </Button>

      {progress.status === "failed" ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-3 rounded-2xl border border-red-500/30 bg-red-500/5 px-8 py-14 text-center"
        >
          <AlertTriangle className="h-8 w-8 text-red-400" />
          <p className="font-display text-lg text-slate-100">Não foi possível processar essa música</p>
          <p className="max-w-md font-body text-sm text-slate-500">{progress.message}</p>
          <Button variant="secondary" onClick={() => router.push("/")} className="mt-2">
            Tentar com outro arquivo
          </Button>
        </motion.div>
      ) : !isTerminal ? (
        <ProgressPanel status={progress.status} percent={progress.percent} message={progress.message} />
      ) : isLoading || !job ? (
        <ProgressPanel status="post_processing" percent={98} message="Carregando resultado..." />
      ) : (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          <div>
            <h1 className="font-display text-2xl font-semibold text-slate-50">{job.original_filename}</h1>
            <p className="font-mono text-xs text-slate-500">engine: {job.engine}</p>
          </div>

          {job.analysis && <AnalysisSummary analysis={job.analysis} />}

          <StemPlayer stems={job.stems} />
        </motion.div>
      )}
    </main>
  );
}
