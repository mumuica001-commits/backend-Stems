"""
Engine de DESENVOLVIMENTO/TESTE — NÃO é separação por IA.

Existe por um motivo prático: os engines de IA (Demucs, MDX-Net) dependem de
baixar gigabytes de pesos de modelo na primeira execução. Isso é ótimo em
produção, mas trava qualquer tentativa de "só testar se o app funciona"
num ambiente sem acesso a esses hosts (ex: CI restrito, sandbox, ou só
enquanto o download dos modelos de produção não terminou).

Este engine usa técnicas CLÁSSICAS de DSP (sem machine learning):

  - drums / other: separação harmônico-percussiva (HPSS — Fitzgerald 2010),
    via mediana em janelas horizontais (harmônico) vs verticais (percussivo)
    no espectrograma. É um algoritmo real e conhecido em MIR, só que muito
    mais simples e menos preciso que um modelo treinado.
  - vocals: extração por cancelamento de fase mid/side — subtrai o canal
    "side" do "mid" pra reduzir conteúdo centralizado no estéreo (técnica
    clássica de "karaokê" dos anos 90/2000). Só funciona em áudio estéreo
    e é facilmente enganada por baixo/bumbo também centralizados.
  - bass: componente harmônico passado por filtro passa-baixa.
  - guitar/piano: aproximações grosseiras por banda de frequência do
    componente harmônico restante — isso é, na prática, "other" dividido
    ao meio por frequência, não separação real por instrumento.

A confiança retornada para stems deste engine é sempre penalizada (teto de
0.55) porque não há classificador nem modelo por trás — é só um teste de
integração do pipeline, e isso é comunicado no dashboard também via
`job.engine == "dev_dsp_mock"`.
"""
from __future__ import annotations

import os

import librosa
import numpy as np
import soundfile as sf

from app.domain.entities import Stem, StemKind
from app.infrastructure.separation.base import ProgressCallback, SeparationEngine, SeparationProgress

_MAX_CONFIDENCE = 0.55  # nunca finge ser tão bom quanto um engine de IA de verdade


class DSPMockEngine(SeparationEngine):
    @property
    def name(self) -> str:
        return "dev_dsp_mock"

    @property
    def supported_stems(self) -> list[str]:
        return ["vocals", "drums", "bass", "guitar", "piano", "other"]

    def is_available(self) -> bool:
        return True  # não depende de pesos externos — sempre disponível

    def separate(
        self,
        input_path: str,
        output_dir: str,
        on_progress: ProgressCallback | None = None,
    ) -> list[Stem]:
        def _report(percent: float, message: str) -> None:
            if on_progress:
                on_progress(SeparationProgress(percent=percent, message=message))

        _report(5, "Carregando áudio (engine de teste, sem IA)...")
        y, sr = librosa.load(input_path, sr=None, mono=False)
        if y.ndim == 1:
            y = np.stack([y, y])  # trata mono como "estéreo" duplicado

        mixture = y.astype(np.float32)
        mono_mix = mixture.mean(axis=0)

        _report(20, "Separação harmônico-percussiva (HPSS)...")
        harmonic, percussive = librosa.effects.hpss(mono_mix)

        _report(40, "Extraindo vocal por cancelamento mid/side...")
        vocals = self._extract_vocals_mid_side(mixture)

        _report(55, "Filtrando grave (bass)...")
        bass = self._lowpass(harmonic, sr, cutoff=250)

        _report(70, "Dividindo bandas restantes (guitar/piano aproximados)...")
        mid_band_residual = harmonic - bass
        guitar = self._bandpass(mid_band_residual, sr, low=250, high=1200)
        piano = mid_band_residual - guitar

        os.makedirs(output_dir, exist_ok=True)
        stems_mono = {
            "vocals": vocals,
            "drums": percussive,
            "bass": bass,
            "guitar": guitar,
            "piano": piano,
            "other": harmonic * 0.15,  # resíduo pequeno — a maior parte já foi alocada acima
        }

        stems: list[Stem] = []
        total = len(stems_mono)
        for idx, (stem_name, audio_mono) in enumerate(stems_mono.items(), start=1):
            _report(70 + int(25 * idx / total), f"Renderizando '{stem_name}'...")

            stereo = np.stack([audio_mono, audio_mono])
            out_path = os.path.join(output_dir, f"{stem_name}.wav")
            sf.write(out_path, stereo.T, samplerate=sr)

            confidence = min(self._energy_confidence(audio_mono, mono_mix), _MAX_CONFIDENCE)

            stems.append(
                Stem(
                    kind=StemKind(stem_name),
                    file_path=out_path,
                    confidence=confidence,
                    duration_seconds=len(audio_mono) / sr,
                    sample_rate=sr,
                    channels=2,
                )
            )

        _report(100, "Separação de teste concluída (sem IA — use Demucs/MDX-Net para qualidade real).")
        return stems

    @staticmethod
    def _extract_vocals_mid_side(stereo: np.ndarray) -> np.ndarray:
        left, right = stereo[0], stereo[1]
        n = min(len(left), len(right))
        side = left[:n] - right[:n]  # conteúdo NÃO centralizado
        mid = (left[:n] + right[:n]) / 2  # conteúdo centralizado (onde o vocal costuma estar)
        # vocal ~ mid com o "side" atenuado subtraído — aproximação crua
        return mid - 0.3 * np.abs(side)

    @staticmethod
    def _lowpass(signal: np.ndarray, sr: int, cutoff: float) -> np.ndarray:
        from scipy.signal import butter, filtfilt

        b, a = butter(4, cutoff / (sr / 2), btype="low")
        return filtfilt(b, a, signal).astype(np.float32)

    @staticmethod
    def _bandpass(signal: np.ndarray, sr: int, low: float, high: float) -> np.ndarray:
        from scipy.signal import butter, filtfilt

        b, a = butter(4, [low / (sr / 2), high / (sr / 2)], btype="band")
        return filtfilt(b, a, signal).astype(np.float32)

    @staticmethod
    def _energy_confidence(stem: np.ndarray, mixture: np.ndarray) -> float:
        eps = 1e-8
        ratio = float(np.mean(stem.astype(np.float64) ** 2)) / (float(np.mean(mixture.astype(np.float64) ** 2)) + eps)
        return float(np.clip(0.15 + ratio, 0.05, 1.0))
