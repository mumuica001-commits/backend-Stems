"""
Detecção de downbeats (primeiro tempo do compasso).

Abordagem: para cada beat detectado, mede a energia do onset naquele
instante. Testa agrupamentos de 3 e 4 beats e escolhe o período cuja
posição inicial tem energia média mais alta que as demais posições
do grupo — downbeats tendem a ser mais "fortes" que os outros tempos.

É uma heurística real e usada em MIR introdutório (não é o
state-of-the-art de deep learning tipo madmom's DBNDownBeatTracker,
mas funciona sem dependências pesadas adicionais e sem GPU).
"""
from __future__ import annotations

import numpy as np
import librosa


def detect_downbeats(y: np.ndarray, sr: int, beat_times: list[float]) -> tuple[list[float], str]:
    if len(beat_times) < 8:
        return beat_times[:1] if beat_times else [], "4/4"

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_times = librosa.frames_to_time(np.arange(len(onset_env)), sr=sr)

    def strength_at(t: float) -> float:
        idx = int(np.searchsorted(onset_times, t))
        idx = min(idx, len(onset_env) - 1)
        return float(onset_env[idx])

    beat_strengths = [strength_at(t) for t in beat_times]

    best_period = 4
    best_score = -np.inf
    best_offset = 0

    for period in (3, 4):
        for offset in range(period):
            positions = beat_strengths[offset::period]
            others = [
                s
                for i, s in enumerate(beat_strengths)
                if (i - offset) % period != 0
            ]
            if not positions or not others:
                continue
            score = float(np.mean(positions)) - float(np.mean(others))
            if score > best_score:
                best_score = score
                best_period = period
                best_offset = offset

    downbeats = beat_times[best_offset::best_period]
    time_signature = "3/4" if best_period == 3 else "4/4"
    return downbeats, time_signature
