"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { SpectralBars } from "@/components/ui/spectral-bars";
import { DropZone } from "@/components/upload/drop-zone";
import { EngineSelector } from "@/components/upload/engine-selector";
import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass-panel";
import { fetchEngines, uploadAudio, ApiError } from "@/lib/api";
import type { EngineId } from "@/lib/types";
import { Sparkles, Loader2 } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [engine, setEngine] = useState<EngineId>("htdemucs_6s");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: engines, isLoading: enginesLoading } = useQuery({
    queryKey: ["engines"],
    queryFn: fetchEngines,
  });

  const handleUpload = useCallback(async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      const { job_id } = await uploadAudio(file, engine);
      router.push(`/jobs/view?id=${job_id}`); // <--- Agora usando a variável correta!
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Falha ao enviar o arquivo. Tente novamente.");
      setIsUploading(false);
    }
  }, [file, engine, router]);
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col items-center text-center"
      >
        <SpectralBars barCount={40} className="mb-8 h-16 opacity-90" />

        <div className="mb-3 flex items-center gap-2 rounded-full border border-base-border bg-base-panelSolid px-3 py-1">
          <Sparkles className="h-3.5 w-3.5 text-amber-400" />
          <span className="font-mono text-[11px] uppercase tracking-wider text-slate-400">
            100% gratuito &amp; open-source
          </span>
        </div>

        <h1 className="font-display text-4xl font-semibold tracking-tight text-slate-50 sm:text-5xl">
          Separe qualquer música
          <br />
          <span className="bg-spectral-gradient bg-clip-text text-transparent">em stems, com IA</span>
        </h1>
        <p className="mt-4 max-w-xl font-body text-base text-slate-400">
          Vocal, bateria, baixo, guitarra e piano — isolados com os melhores modelos
          open-source, mais BPM, tonalidade e progressão de acordes. Sem custo, sem cadastro.
        </p>
      </motion.div>

      <GlassPanel className="mt-12 w-full space-y-6 p-6">
        <DropZone onFileSelected={setFile} selectedFile={file} onClear={() => setFile(null)} disabled={isUploading} />

        <EngineSelector engines={engines ?? []} selected={engine} onSelect={setEngine} isLoading={enginesLoading} />

        {error && <p className="font-body text-sm text-red-400">{error}</p>}

        <Button
          variant="primary"
          size="lg"
          className="w-full"
          disabled={!file || isUploading}
          onClick={handleUpload}
        >
          {isUploading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Enviando...
            </>
          ) : (
            "Separar stems"
          )}
        </Button>
      </GlassPanel>
    </main>
  );
}
