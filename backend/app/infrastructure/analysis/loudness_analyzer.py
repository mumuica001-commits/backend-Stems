"""
Medição de loudness seguindo o padrão broadcast ITU-R BS.1770
(o mesmo usado por Spotify/YouTube para normalização) via `pyloudnorm`.
"""
from __future__ import annotations

import numpy as np
import pyloudnorm as pyln


def measure_loudness(y: np.ndarray, sr: int) -> tuple[float, float]:
    """
    Retorna (lufs_integrado, rms_db).
    `y` deve ser (samples,) ou (samples, channels) — pyloudnorm espera
    shape (samples,) ou (samples, channels), não (channels, samples).
    """
    audio = y.T if y.ndim > 1 and y.shape[0] < y.shape[1] else y

    meter = pyln.Meter(sr)
    lufs = meter.integrated_loudness(audio)

    rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
    rms_db = 20 * np.log10(max(rms, 1e-8))

    # integrated_loudness retorna -inf para silêncio total
    lufs_clean = lufs if np.isfinite(lufs) else -70.0

    return round(float(lufs_clean), 2), round(float(rms_db), 2)
