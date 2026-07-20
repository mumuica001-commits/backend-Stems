export type JobStatus =
  | "queued"
  | "analyzing"
  | "separating"
  | "post_processing"
  | "completed"
  | "failed";

export type StemKind = "vocals" | "backing_vocals" | "drums" | "bass" | "guitar" | "piano" | "other";

export type EngineId = "htdemucs_6s" | "htdemucs_ft" | "mdx_net_karaoke_2" | "mdx23c" | "dev_dsp_mock";

export interface EngineInfo {
  id: EngineId;
  name?: string;
  supported_stems: string[];
  available: boolean;
}

export interface StemResponse {
  kind: StemKind;
  confidence: number;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  download_url: string;
}

export interface ChordEvent {
  time: number;
  chord: string;
  duration: number;
  confidence: number;
}

export interface AnalysisResponse {
  bpm: number | null;
  bpm_confidence: number;
  key: string | null;
  key_confidence: number;
  time_signature: string | null;
  downbeats: number[];
  chords: ChordEvent[];
  lufs_integrated: number | null;
  rms_db: number | null;
  duration_seconds: number | null;
}

export interface JobResponse {
  id: string;
  original_filename: string;
  engine: string;
  status: JobStatus;
  progress_percent: number;
  stage_message: string;
  stems: StemResponse[];
  analysis: AnalysisResponse | null;
  error_message: string | null;
}

export interface JobProgressMessage {
  job_id?: string;
  status?: JobStatus;
  percent?: number;
  message?: string;
  type?: "heartbeat";
  error?: string;
}

export const STEM_LABELS: Record<StemKind, string> = {
  vocals: "Vocal",
  backing_vocals: "Backing Vocal",
  drums: "Bateria",
  bass: "Baixo",
  guitar: "Guitarra",
  piano: "Piano",
  other: "Outros",
};
