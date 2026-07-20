"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";
import { cn } from "@/lib/utils";

interface SpectralBarsProps {
  barCount?: number;
  active?: boolean;
  className?: string;
  /** 0..100 — quando definido, as barras à esquerda desse ponto ficam "acesas" */
  progress?: number;
}

export function SpectralBars({ barCount = 48, active = true, className, progress }: SpectralBarsProps) {
  // alturas pseudo-aleatórias mas estáveis (não recalcula a cada render)
  const heights = useMemo(
    () => Array.from({ length: barCount }, (_, i) => 0.25 + Math.abs(Math.sin(i * 12.9898) % 1) * 0.75),
    [barCount]
  );

  return (
    <div className={cn("flex items-end gap-[3px] h-24", className)} aria-hidden="true">
      {heights.map((h, i) => {
        const barProgress = ((i + 1) / barCount) * 100;
        const isLit = progress === undefined || barProgress <= progress;

        return (
          <motion.div
            key={i}
            className="w-1 rounded-full"
            style={{
              height: `${h * 100}%`,
              background: isLit
                ? `linear-gradient(180deg, #F59E0B 0%, #DB2777 55%, #6D28D9 100%)`
                : "rgba(255,255,255,0.08)",
            }}
            animate={
              active && isLit
                ? { scaleY: [0.4, 1, 0.4] }
                : { scaleY: h }
            }
            transition={
              active && isLit
                ? { duration: 0.9 + (i % 5) * 0.15, repeat: Infinity, ease: "easeInOut", delay: i * 0.02 }
                : { duration: 0.3 }
            }
          />
        );
      })}
    </div>
  );
}
