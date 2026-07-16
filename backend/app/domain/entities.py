"""
Domain entities — STEMS AI

Camada de domínio: não conhece FastAPI, Redis, Demucs ou qualquer detalhe
de infraestrutura. Apenas regras e formas de negócio.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    SEPARATING = "separating"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SeparationEngineName(str, Enum):
    """Modelos de separação suportados. Trocáveis em runtime por job."""
    DEMUCS_HTDEMUCS_6S = "htdemucs_6s"     # vocals, drums, bass, guitar, piano, other
    DEMUCS_HTDEMUCS_FT = "htdemucs_ft"     # fine-tuned, 4 stems, maior qualidade
    MDX_NET_KARAOKE_2 = "mdx_net_karaoke_2"  # especializado vocal/instrumental
    MDX23C = "mdx23c"                       # boa qualidade em bass/drums
    DEV_DSP_MOCK = "dev_dsp_mock"           # DSP clássico, sem pesos de IA — ver dsp_mock_engine.py


class StemKind(str, Enum):
    """
    Stems que podem ser REALMENTE isolados por separação de fonte.
    Qualquer coisa mais granular (ex: 'crash' vs 'ride', 'trumpet' vs 'trombone')
    não é separação — é tagging/detecção dentro do stem 'drums' ou 'other',
    tratado por AnalysisResult.instrument_events, não por Stem.
    """
    VOCALS = "vocals"
    BACKING_VOCALS = "backing_vocals"   # apenas quando o engine suporta (ex: mdx karaoke variants)
    DRUMS = "drums"
    BASS = "bass"
    GUITAR = "guitar"
    PIANO = "piano"
    OTHER = "other"


@dataclass
class Stem:
    kind: StemKind
    file_path: str
    confidence: float  # 0..1 — heurística baseada em energia residual do engine
    duration_seconds: float
    sample_rate: int
    channels: int


@dataclass
class InstrumentEvent:
    """
    Evento pontual de um instrumento detectado DENTRO de um stem
    (ex: onset de 'kick' dentro do stem 'drums'), via classificação,
    não separação de áudio.
    """
    label: str          # ex: "kick", "snare", "hihat_closed"
    parent_stem: StemKind
    timestamp_seconds: float
    confidence: float


@dataclass
class MusicAnalysis:
    bpm: float | None = None
    bpm_confidence: float = 0.0
    key: str | None = None            # ex: "A minor"
    key_confidence: float = 0.0
    time_signature: str | None = None  # ex: "4/4"
    downbeats: list[float] = field(default_factory=list)
    chords: list[dict] = field(default_factory=list)  # [{"time":0.0,"chord":"Am","duration":1.2}]
    lufs_integrated: float | None = None
    rms_db: float | None = None
    duration_seconds: float | None = None


@dataclass
class SeparationJob:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_filename: str = ""
    source_path: str = ""
    engine: SeparationEngineName = SeparationEngineName.DEMUCS_HTDEMUCS_6S
    status: JobStatus = JobStatus.QUEUED
    progress_percent: float = 0.0
    stage_message: str = ""
    stems: list[Stem] = field(default_factory=list)
    instrument_events: list[InstrumentEvent] = field(default_factory=list)
    analysis: MusicAnalysis | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def mark_progress(self, status: JobStatus, percent: float, message: str) -> None:
        self.status = status
        self.progress_percent = percent
        self.stage_message = message
        self.updated_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        self.status = JobStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        self.status = JobStatus.COMPLETED
        self.progress_percent = 100.0
        self.updated_at = datetime.now(timezone.utc)
