import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

export function GlassPanel({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-base-border bg-base-panel backdrop-blur-glass shadow-[0_8px_32px_rgba(0,0,0,0.35)]",
        className
      )}
      {...props}
    />
  );
}
