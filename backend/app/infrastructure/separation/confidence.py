"""
Estimador de confiança por stem.

IMPORTANTE (honestidade técnica): não existe "score de confiança" nativo
nos modelos de separação — eles não são classificadores, são regressores
de forma de onda. O que fazemos aqui é uma HEURÍSTICA baseada em:

  1. Energia relativa do stem em relação à mistura original
     (um stem quase silencioso em uma música que claramente tem
     aquele instrumento é sinal de baixa confiança).
  2. "Vazamento espectral": o quanto de energia de outros stems
     aparece sobreposta neste, medido por correlação espectral cruzada.

Isso é honesto sobre ser uma aproximação — não uma métrica de SDR real
(que exigiria stems de referência, indisponíveis em inferência).
"""
from __future__ import annotations

import numpy as np


def estimate_stem_confidence(
    stem_audio: np.ndarray,
    mixture_audio: np.ndarray,
    other_stems_audio: list[np.ndarray],
) -> float:
    """
    Retorna um score heurístico em [0, 1].

    stem_audio, mixture_audio, other_stems_audio: arrays float32 mono ou
    estéreo já alinhados em tempo e mesma taxa de amostragem.
    """
    eps = 1e-8

    stem_energy = float(np.mean(stem_audio.astype(np.float64) ** 2))
    mixture_energy = float(np.mean(mixture_audio.astype(np.float64) ** 2)) + eps

    # 1. presença relativa do stem na mistura
    energy_ratio = min(stem_energy / mixture_energy, 1.0)

    # 2. quanto este stem "se parece" com os outros (vazamento espectral)
    leakage_scores = []
    stem_spec = _spectral_envelope(stem_audio)
    for other in other_stems_audio:
        other_spec = _spectral_envelope(other)
        n = min(len(stem_spec), len(other_spec))
        if n == 0:
            continue
        corr = np.corrcoef(stem_spec[:n], other_spec[:n])[0, 1]
        leakage_scores.append(max(corr, 0.0))
    leakage_penalty = float(np.mean(leakage_scores)) if leakage_scores else 0.0

    raw_score = (0.65 * _sigmoid_boost(energy_ratio)) + (0.35 * (1.0 - leakage_penalty))
    return float(np.clip(raw_score, 0.02, 0.99))


def _spectral_envelope(audio: np.ndarray, n_fft: int = 2048, hop: int = 512) -> np.ndarray:
    mono = audio.mean(axis=0) if audio.ndim > 1 else audio
    if len(mono) < n_fft:
        return np.abs(np.fft.rfft(mono, n=n_fft))
    frames = [
        np.abs(np.fft.rfft(mono[i : i + n_fft] * np.hanning(n_fft)))
        for i in range(0, len(mono) - n_fft, hop * 20)  # subsample pra custo baixo
    ]
    if not frames:
        return np.abs(np.fft.rfft(mono, n=n_fft))
    return np.mean(frames, axis=0)


def _sigmoid_boost(x: float, k: float = 6.0, midpoint: float = 0.15) -> float:
    """Energias pequenas mas reais (ex: hi-hat) não devem ser punidas linearmente."""
    return float(1.0 / (1.0 + np.exp(-k * (x - midpoint))))
