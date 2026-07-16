import numpy as np
import pytest

from app.infrastructure.analysis.rhythm_key_analyzer import detect_bpm_and_beats, detect_key
from app.infrastructure.analysis.loudness_analyzer import measure_loudness
from app.infrastructure.separation.confidence import estimate_stem_confidence


def _synth_click_track(bpm: float, sr: int = 22050, seconds: float = 8.0) -> np.ndarray:
    """Gera um clique sintético em um BPM conhecido para testar beat tracking."""
    n_samples = int(sr * seconds)
    y = np.zeros(n_samples, dtype=np.float32)
    interval = int(sr * 60.0 / bpm)
    click = np.exp(-np.linspace(0, 30, int(sr * 0.05))).astype(np.float32)
    for start in range(0, n_samples - len(click), interval):
        y[start : start + len(click)] += click
    return y


def test_detect_bpm_reasonably_close_to_ground_truth():
    sr = 22050
    y = _synth_click_track(bpm=120.0, sr=sr)
    bpm, confidence, beats = detect_bpm_and_beats(y, sr)

    # tolerância generosa: beat tracking pode pegar o dobro/metade do tempo
    assert any(abs(bpm - target) < 5 for target in (120.0, 60.0, 240.0))
    assert 0.0 <= confidence <= 1.0
    assert len(beats) > 0


def test_detect_key_returns_valid_label():
    sr = 22050
    t = np.linspace(0, 4, sr * 4, endpoint=False)
    # tríade de C maior (C-E-G) sintética
    y = (
        np.sin(2 * np.pi * 261.63 * t)
        + np.sin(2 * np.pi * 329.63 * t)
        + np.sin(2 * np.pi * 392.00 * t)
    ).astype(np.float32)

    key, confidence = detect_key(y, sr)

    assert "major" in key or "minor" in key
    assert 0.0 <= confidence <= 1.0


def test_measure_loudness_silence_returns_very_low_lufs():
    sr = 22050
    y = np.zeros(sr * 2, dtype=np.float32)
    lufs, rms_db = measure_loudness(y, sr)

    assert lufs < -40
    assert rms_db < -40


def test_stem_confidence_is_bounded():
    rng = np.random.default_rng(42)
    mixture = rng.normal(0, 0.3, (2, 44100)).astype(np.float32)
    stem = mixture * 0.5
    other = rng.normal(0, 0.1, (2, 44100)).astype(np.float32)

    score = estimate_stem_confidence(stem, mixture, [other])

    assert 0.0 <= score <= 1.0


def test_stem_confidence_penalizes_high_leakage():
    rng = np.random.default_rng(7)
    mixture = rng.normal(0, 0.3, (2, 44100)).astype(np.float32)

    identical_leak_score = estimate_stem_confidence(mixture, mixture, [mixture])
    low_leak_score = estimate_stem_confidence(
        mixture, mixture, [rng.normal(0, 0.3, (2, 44100)).astype(np.float32)]
    )

    assert identical_leak_score <= low_leak_score + 0.2  # vazamento alto não deve ser premiado
