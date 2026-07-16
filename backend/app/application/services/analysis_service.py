from __future__ import annotations

import librosa

from app.core.logging import get_logger
from app.domain.entities import MusicAnalysis
from app.infrastructure.analysis.chord_detector import detect_chords
from app.infrastructure.analysis.downbeat_detector import detect_downbeats
from app.infrastructure.analysis.loudness_analyzer import measure_loudness
from app.infrastructure.analysis.rhythm_key_analyzer import detect_bpm_and_beats, detect_key

logger = get_logger(__name__)


class AnalysisService:
    """Orquestra todos os detectores de análise musical sobre o áudio original."""

    def analyze(self, audio_path: str) -> MusicAnalysis:
        logger.info("Analisando áudio: %s", audio_path)

        y, sr = librosa.load(audio_path, sr=None, mono=True)
        duration = float(len(y) / sr)

        bpm, bpm_confidence, beat_times = detect_bpm_and_beats(y, sr)
        key, key_confidence = detect_key(y, sr)
        downbeats, time_signature = detect_downbeats(y, sr, beat_times)
        chords = detect_chords(y, sr)
        lufs, rms_db = measure_loudness(y, sr)

        return MusicAnalysis(
            bpm=bpm,
            bpm_confidence=bpm_confidence,
            key=key,
            key_confidence=key_confidence,
            time_signature=time_signature,
            downbeats=downbeats,
            chords=chords,
            lufs_integrated=lufs,
            rms_db=rms_db,
            duration_seconds=duration,
        )
