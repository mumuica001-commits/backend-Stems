"""
Detecção de progressão de acordes.

Método: template matching de chroma — para cada janela de tempo,
calcula o vetor de chroma (12 classes de altura) e compara por
correlação com templates binários de tríades maiores/menores/
diminutas/aumentadas nas 12 tônicas (48 templates).

Isto é a abordagem clássica (Fujishima 1999 / template matching)
e funciona bem para música tonal com harmonia relativamente estável
por compasso. Não lida bem com jazz muito cromático/extensões — isso
ficaria para uma Fase futura com um modelo de deep learning (ex: um
Chord-CNN treinado em datasets tipo Isophonics).
"""
from __future__ import annotations

import numpy as np
import librosa

_PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

_TRIAD_INTERVALS = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
}


def _build_templates() -> dict[str, np.ndarray]:
    templates = {}
    for root in range(12):
        for quality, intervals in _TRIAD_INTERVALS.items():
            vec = np.zeros(12)
            for interval in intervals:
                vec[(root + interval) % 12] = 1.0
            label = _PITCH_CLASSES[root] + ("" if quality == "maj" else {
                "min": "m", "dim": "dim", "aug": "aug"
            }[quality])
            templates[label] = vec
    return templates


_TEMPLATES = _build_templates()


def detect_chords(y: np.ndarray, sr: int, window_seconds: float = 1.0) -> list[dict]:
    hop_length = 2048
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    frame_times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop_length)

    frames_per_window = max(1, int(window_seconds * sr / hop_length))

    chords: list[dict] = []
    for start in range(0, chroma.shape[1], frames_per_window):
        end = min(start + frames_per_window, chroma.shape[1])
        window_chroma = chroma[:, start:end].mean(axis=1)
        if window_chroma.sum() < 1e-6:
            continue

        norm_chroma = window_chroma / (np.linalg.norm(window_chroma) + 1e-8)

        best_label, best_score = "N", -np.inf
        for label, template in _TEMPLATES.items():
            norm_template = template / np.linalg.norm(template)
            score = float(np.dot(norm_chroma, norm_template))
            if score > best_score:
                best_score = score
                best_label = label

        chords.append(
            {
                "time": round(float(frame_times[start]), 3),
                "chord": best_label,
                "duration": round(float(frame_times[min(end, len(frame_times) - 1)] - frame_times[start]), 3),
                "confidence": round(float(np.clip(best_score, 0, 1)), 3),
            }
        )

    return _merge_consecutive_chords(chords)


def _merge_consecutive_chords(chords: list[dict]) -> list[dict]:
    """Funde janelas consecutivas com o mesmo acorde detectado."""
    if not chords:
        return []
    merged = [chords[0].copy()]
    for chord in chords[1:]:
        last = merged[-1]
        if chord["chord"] == last["chord"]:
            last["duration"] = round(chord["time"] + chord["duration"] - last["time"], 3)
        else:
            merged.append(chord.copy())
    return merged
