import type { EngineId, EngineInfo, JobResponse } from "./types";

// 1. Lemos a URL do backend do Railway. Se não encontrar no .env, usa o link direto como fallback.
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "backend-stems-production.up.railway.app";
const API_BASE = `${BACKEND_URL}/api/v1`;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail || `Erro ${res.status}`, res.status);
  }
  return res.json();
}

export async function uploadAudio(file: File, engine: EngineId): Promise<{ job_id: string; status: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("engine", engine);

  // Agora envia diretamente para o Railway
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
  return handleResponse(res);
}

export async function fetchJob(jobId: string): Promise<JobResponse> {
  // Agora busca diretamente do Railway
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  return handleResponse(res);
}

export async function fetchEngines(): Promise<EngineInfo[]> {
  // Agora busca as engines diretamente do Railway
  const res = await fetch(`${API_BASE}/engines`);
  return handleResponse(res);
}

export function stemDownloadUrl(downloadUrl: string): string {
  // Ajusta o link de download para apontar para o Railway se for uma rota interna /api
  if (downloadUrl.startsWith("http")) return downloadUrl;
  
  const cleanPath = downloadUrl.startsWith("/") ? downloadUrl : `/${downloadUrl}`;
  // Se o link de download já começar com "/api", tiramos para não duplicar com o API_BASE
  const finalPath = cleanPath.startsWith("/api/v1") ? cleanPath.replace("/api/v1", "") : cleanPath;
  
  return `${API_BASE}${finalPath}`;
}

export function jobWebSocketUrl(jobId: string): string {
  // Se o backend for HTTPS, o WS precisa ser WSS (seguro)
  const isHttps = BACKEND_URL.startsWith("https://");
  const protocol = isHttps ? "wss" : "ws";
  
  // Extraímos apenas o host (ex: backend-stems-production.up.railway.app) tirando o "https://" da frente
  const cleanHost = BACKEND_URL.replace(/^https?:\/\//, "");
  
  return `${protocol}://${cleanHost}/ws/jobs/${jobId}`;
}