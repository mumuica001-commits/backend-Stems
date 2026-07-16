"""
Engine de separação MDX-Net.

MDX-Net (Kim et al. / vencedor do Sony Music Demixing Challenge) é
tipicamente distribuído como checkpoints .onnx pela comunidade
(ex: UVR — Ultimate Vocal Remover). Aqui implementamos o inference
runner: STFT em chunks com overlap, passa pela rede via onnxruntime,
reconstrói via ISTFT com janela de crossfade.

Os pesos (.onnx) NÃO são baixados automaticamente — não há uma fonte
oficial única redistribuível. O operador do serviço deve colocar o
arquivo em `mdx_model_cache_dir/<model_key>.onnx`. Ver README para links.
"""
from __future__ import annotations

import os

import numpy as np
import soundfile as sf

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.entities import Stem, StemKind
from app.domain.exceptions import SeparationEngineError
from app.infrastructure.separation.base import ProgressCallback, SeparationEngine, SeparationProgress
from app.infrastructure.separation.confidence import estimate_stem_confidence

logger = get_logger(__name__)

# cada "modelo" MDX é especializado em separar 1 par (alvo vs resto)
_MDX_MODEL_TARGETS = {
    "mdx_net_karaoke_2": ("vocals", "instrumental"),
    "mdx23c": ("bass", "no_bass"),
}


class MDXNetEngine(SeparationEngine):
    N_FFT = 6144
    HOP_LENGTH = 1024
    CHUNK_SECONDS = 15
    OVERLAP_SECONDS = 2

    def __init__(self, model_key: str = "mdx_net_karaoke_2"):
        if model_key not in _MDX_MODEL_TARGETS:
            raise SeparationEngineError(model_key, "modelo MDX-Net desconhecido")
        self._model_key = model_key
        self._settings = get_settings()
        self._session = None

    @property
    def name(self) -> str:
        return self._model_key

    @property
    def supported_stems(self) -> list[str]:
        return list(_MDX_MODEL_TARGETS[self._model_key])

    def _weights_path(self) -> str:
        return os.path.join(self._settings.mdx_model_cache_dir, f"{self._model_key}.onnx")

    def is_available(self) -> bool:
        try:
            import onnxruntime  # noqa: F401
        except ImportError:
            logger.warning("Pacote 'onnxruntime' não instalado — MDX-Net indisponível.")
            return False
        return os.path.isfile(self._weights_path())

    def _load_session(self):
        if self._session is not None:
            return self._session

        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise SeparationEngineError(self.name, "pacote 'onnxruntime' não instalado") from exc

        weights_path = self._weights_path()
        if not os.path.isfile(weights_path):
            raise SeparationEngineError(
                self.name,
                f"pesos não encontrados em '{weights_path}'. Veja README para obtê-los.",
            )

        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] \
            if self._settings.device == "cuda" else ["CPUExecutionProvider"]
        self._session = ort.InferenceSession(weights_path, providers=providers)
        return self._session

    def separate(
        self,
        input_path: str,
        output_dir: str,
        on_progress: ProgressCallback | None = None,
    ) -> list[Stem]:
        session = self._load_session()

        def _report(percent: float, message: str) -> None:
            if on_progress:
                on_progress(SeparationProgress(percent=percent, message=message))

        _report(5, "Carregando áudio...")
        mixture, sample_rate = sf.read(input_path, always_2d=True)  # (samples, channels)
        mixture = mixture.T.astype(np.float32)  # (channels, samples)

        target_name, residual_name = _MDX_MODEL_TARGETS[self._model_key]

        chunk_len = int(self.CHUNK_SECONDS * sample_rate)
        overlap_len = int(self.OVERLAP_SECONDS * sample_rate)
        stride = chunk_len - overlap_len

        target_audio = np.zeros_like(mixture)
        weight_sum = np.zeros(mixture.shape[-1], dtype=np.float32)
        window = np.hanning(chunk_len).astype(np.float32)

        n_chunks = max(1, int(np.ceil(mixture.shape[-1] / stride)))
        input_name = session.get_inputs()[0].name

        for i, start in enumerate(range(0, mixture.shape[-1], stride)):
            _report(10 + int(80 * i / n_chunks), f"Processando chunk {i + 1}/{n_chunks}...")

            end = min(start + chunk_len, mixture.shape[-1])
            chunk = mixture[:, start:end]
            pad_len = chunk_len - chunk.shape[-1]
            if pad_len > 0:
                chunk = np.pad(chunk, ((0, 0), (0, pad_len)))

            spec = self._stft(chunk)
            try:
                pred_spec = session.run(None, {input_name: spec[np.newaxis, ...]})[0][0]
            except Exception as exc:
                raise SeparationEngineError(self.name, f"falha na inferência ONNX: {exc}") from exc

            pred_audio = self._istft(pred_spec, length=chunk_len)
            w = window[: end - start]
            target_audio[:, start:end] += pred_audio[:, : end - start] * w
            weight_sum[start:end] += w

        weight_sum = np.maximum(weight_sum, 1e-8)
        target_audio = target_audio / weight_sum
        residual_audio = mixture - target_audio

        os.makedirs(output_dir, exist_ok=True)
        target_path = os.path.join(output_dir, f"{target_name}.wav")
        residual_path = os.path.join(output_dir, f"{residual_name}.wav")
        sf.write(target_path, target_audio.T, samplerate=sample_rate)
        sf.write(residual_path, residual_audio.T, samplerate=sample_rate)

        duration = mixture.shape[-1] / sample_rate
        target_conf = estimate_stem_confidence(target_audio, mixture, [residual_audio])
        residual_conf = estimate_stem_confidence(residual_audio, mixture, [target_audio])

        _report(100, "Separação concluída.")

        return [
            Stem(
                kind=self._name_to_kind(target_name),
                file_path=target_path,
                confidence=target_conf,
                duration_seconds=duration,
                sample_rate=sample_rate,
                channels=mixture.shape[0],
            ),
            Stem(
                kind=self._name_to_kind(residual_name),
                file_path=residual_path,
                confidence=residual_conf,
                duration_seconds=duration,
                sample_rate=sample_rate,
                channels=mixture.shape[0],
            ),
        ]

    @staticmethod
    def _name_to_kind(name: str) -> StemKind:
        return {"vocals": StemKind.VOCALS, "bass": StemKind.BASS}.get(name, StemKind.OTHER)

    def _stft(self, audio: np.ndarray) -> np.ndarray:
        specs = [
            np.abs(np.fft.rfft(audio[ch], n=self.N_FFT))
            for ch in range(audio.shape[0])
        ]
        return np.stack(specs, axis=0).astype(np.float32)

    def _istft(self, spec: np.ndarray, length: int) -> np.ndarray:
        channels = [
            np.fft.irfft(spec[ch], n=self.N_FFT)[:length]
            for ch in range(spec.shape[0])
        ]
        return np.stack(channels, axis=0).astype(np.float32)
