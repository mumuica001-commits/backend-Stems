"use client";

import { useCallback, useRef, useState } from "react";
import { motion } from "framer-motion";
import { UploadCloud, FileAudio, X } from "lucide-react";
import { cn } from "@/lib/utils";

const ACCEPTED_EXTENSIONS = [".mp3", ".wav", ".flac", ".aiff", ".aac", ".ogg", ".m4a"];

interface DropZoneProps {
  onFileSelected: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
  disabled?: boolean;
}

export function DropZone({ onFileSelected, selectedFile, onClear, disabled }: DropZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const isValidFile = useCallback((file: File) => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    return ACCEPTED_EXTENSIONS.includes(ext);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file && isValidFile(file)) onFileSelected(file);
    },
    [onFileSelected, isValidFile]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file && isValidFile(file)) onFileSelected(file);
    },
    [onFileSelected, isValidFile]
  );

  if (selectedFile) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between rounded-2xl border border-base-border bg-base-panelSolid px-6 py-5"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-spectral-gradient">
            <FileAudio className="h-5 w-5 text-white" />
          </div>
          <div className="min-w-0">
            <p className="truncate font-body text-sm text-slate-100">{selectedFile.name}</p>
            <p className="font-mono text-xs text-slate-500">
              {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB
            </p>
          </div>
        </div>
        {!disabled && (
          <button
            onClick={onClear}
            className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
            aria-label="Remover arquivo"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </motion.div>
    );
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragActive(true);
      }}
      onDragLeave={() => setIsDragActive(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      className={cn(
        "cursor-pointer rounded-2xl border-2 border-dashed px-6 py-14 text-center transition-colors",
        isDragActive ? "border-spectral-via bg-spectral-via/5" : "border-base-border hover:border-slate-500"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        onChange={handleInputChange}
        className="hidden"
      />
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/5">
        <UploadCloud className="h-6 w-6 text-slate-300" />
      </div>
      <p className="font-display text-lg text-slate-100">Solte sua música aqui</p>
      <p className="mt-1 font-body text-sm text-slate-500">ou clique para escolher um arquivo</p>
      <p className="mt-4 font-mono text-xs uppercase tracking-wider text-slate-600">
        {ACCEPTED_EXTENSIONS.join(" · ")}
      </p>
    </div>
  );
}
