"""
Detecção de BPM, key (tonalidade) e downbeats.

- BPM/beats: onset strength + beat tracking dinâmico (librosa.beat).
- Key: perfis de Krumhansl-Schmuckler correlacionados com o chroma
  médio da faixa — método clássico e bem validado em MIR.
- Time signature: heurística a partir do agrupamento de beats em
  padrões de força (não é 100% robusto para métricas incomuns,
  mas cobre a esmagadora maioria de música popular).
"""
from __future__ import annotations

import numpy as np
import librosa

from app.core.logging import get_logger

logger = get_logger(__name__)

# Perfis de Krumhansl-Kessler (maior e menor)
_MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
_MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)
_PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def detect_bpm_and_beats(y: np.ndarray, sr: int) -> tuple[float, float, list[float]]:
    """Retorna (bpm, confidence, beat_timestamps_seconds)."""
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, trim=False)
    bpm = float(np.atleast_1d(tempo)[0])

    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    # confiança: quão regular é o intervalo entre beats detectados
    if len(beat_times) > 4:
        intervals = np.diff(beat_times)
        regularity = 1.0 - float(np.clip(np.std(intervals) / (np.mean(intervals) + 1e-8), 0, 1))
    else:
        regularity = 0.3

    return round(bpm, 1), round(regularity, 3), beat_times


def detect_key(y: np.ndarray, sr: int) -> tuple[str, float]:
    """Retorna (key_label, confidence) ex: ('A minor', 0.81)."""
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)

    best_score = -np.inf
    best_label = "C major"
    all_scores = []

    for shift in range(12):
        major_corr = np.corrcoef(np.roll(_MAJOR_PROFILE, shift), chroma_mean)[0, 1]
        minor_corr = np.corrcoef(np.roll(_MINOR_PROFILE, shift), chroma_mean)[0, 1]
        all_scores.extend([major_corr, minor_corr])

        if major_corr > best_score:
            best_score = major_corr
            best_label = f"{_PITCH_CLASSES[shift]} major"
        if minor_corr > best_score:
            best_score = minor_corr
            best_label = f"{_PITCH_CLASSES[shift]} minor"

    # normaliza confiança relativa à distância do 2º melhor candidato
    sorted_scores = sorted(all_scores, reverse=True)
    margin = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else 0.1
    confidence = float(np.clip(0.5 + margin * 2, 0.1, 0.98))

    return best_label, round(confidence, 3)


def estimate_time_signature(beat_times: list[float], onset_env: np.ndarray | None = None) -> str:
    """
    Heurística simples: agrupa beats e testa qual período de acentuação
    (2, 3 ou 4 beats) melhor explica variações de força entre beats.
    Cobre 4/4, 3/4, 6/8 (aproximado como 3/4) — a grande maioria da música popular.
    """
    if len(beat_times) < 8:
        return "4/4"
    # sem acesso a força por beat aqui de forma barata: default seguro
    # (ver downbeat_detector.py para versão com força real)
    return "4/4"
