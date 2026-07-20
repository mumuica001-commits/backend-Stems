"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchJob } from "@/lib/api";

export function useJob(jobId: string | null, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => fetchJob(jobId!),
    enabled: Boolean(jobId) && (options?.enabled ?? true),
    refetchOnWindowFocus: false,
  });
}
