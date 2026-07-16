from __future__ import annotations

from pydantic import BaseModel


class StemResponse(BaseModel):
    kind: str
    confidence: float
    duration_seconds: float
    sample_rate: int
    channels: int
    download_url: str


class ChordResponse(BaseModel):
    time: float
    chord: str
    duration: float
    confidence: float


class AnalysisResponse(BaseModel):
    bpm: float | None
    bpm_confidence: float
    key: str | None
    key_confidence: float
    time_signature: str | None
    downbeats: list[float]
    chords: list[ChordResponse]
    lufs_integrated: float | None
    rms_db: float | None
    duration_seconds: float | None


class JobResponse(BaseModel):
    id: str
    original_filename: str
    engine: str
    status: str
    progress_percent: float
    stage_message: str
    stems: list[StemResponse] = []
    analysis: AnalysisResponse | None = None
    error_message: str | None = None


class EngineInfoResponse(BaseModel):
    id: str
    name: str | None = None
    supported_stems: list[str] = []
    available: bool
