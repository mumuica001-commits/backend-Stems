"""
Engine de separação baseado em Demucs (Hybrid Transformer).

Usa o pacote oficial `demucs` (Meta AI / Défossez et al.), via a API
programática `demucs.api.Separator`, disponível a partir do demucs 4.x.

Modelos suportados via `model_name`:
  - "htdemucs_6s": 6 stems (vocals, drums, bass, guitar, piano, other)
  - "htdemucs_ft": 4 stems, fine-tuned, maior qualidade em vocals/bass

Pesos são baixados automaticamente pelo torch.hub na primeira execução
e cacheados em `demucs_model_cache_dir`.
"""
from __future__ import annotations

import os
import time

import numpy as np
import soundfile as sf

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.entities import Stem, StemKind
from app.domain.exceptions import SeparationEngineError
from app.infrastructure.separation.base import ProgressCallback, SeparationEngine, SeparationProgress
from app.infrastructure.separation.confidence import estimate_stem_confidence

logger = get_logger(__name__)

_STEM_NAME_TO_KIND = {
    "vocals": StemKind.VOCALS,
    "drums": StemKind.DRUMS,
    "bass": StemKind.BASS,
    "guitar": StemKind.GUITAR,
    "piano": StemKind.PIANO,
    "other": StemKind.OTHER,
}


class DemucsEngine(SeparationEngine):
    def __init__(self, model_name: str = "htdemucs_6s"):
        self._model_name = model_name
        self._settings = get_settings()
        self._separator = None  # lazy load — modelo é pesado

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def supported_stems(self) -> list[str]:
        if self._model_name == "htdemucs_6s":
            return ["vocals", "drums", "bass", "guitar", "piano", "other"]
        return ["vocals", "drums", "bass", "other"]

    def is_available(self) -> bool:
        try:
            import demucs.api  # noqa: F401
            return True
        except ImportError:
            logger.warning("Pacote 'demucs' não instalado — engine indisponível.")
            return False

    def _load_model(self):
        if self._separator is not None:
            return self._separator

        try:
            from demucs.api import Separator
        except ImportError as exc:
            raise SeparationEngineError(self.name, "pacote 'demucs' não instalado") from exc

        os.makedirs(self._settings.demucs_model_cache_dir, exist_ok=True)
        os.environ.setdefault("TORCH_HOME", self._settings.demucs_model_cache_dir)

        device = self._resolve_device()
        logger.info("Carregando modelo Demucs '%s' em '%s'...", self._model_name, device)

        self._separator = Separator(model=self._model_name, device=device)
        return self._separator

    def _resolve_device(self) -> str:
        if self._settings.device != "cuda":
            return "cpu"
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def separate(
        self,
        input_path: str,
        output_dir: str,
        on_progress: ProgressCallback | None = None,
    ) -> list[Stem]:
        separator = self._load_model()

        def _report(percent: float, message: str) -> None:
            if on_progress:
                on_progress(SeparationProgress(percent=percent, message=message))

        _report(5, f"Carregando áudio para separação com {self.name}...")

        try:
            origin, separated = separator.separate_audio_file(input_path)
        except Exception as exc:  # modelo pode falhar por OOM, formato, etc.
            raise SeparationEngineError(self.name, str(exc)) from exc

        os.makedirs(output_dir, exist_ok=True)
        sample_rate = separator.samplerate
        mixture_np = origin.numpy() if hasattr(origin, "numpy") else np.asarray(origin)

        stems: list[Stem] = []
        stem_arrays: dict[str, np.ndarray] = {
            stem_name: (tensor.numpy() if hasattr(tensor, "numpy") else np.asarray(tensor))
            for stem_name, tensor in separated.items()
        }

        total = len(stem_arrays)
        for idx, (stem_name, audio_array) in enumerate(stem_arrays.items(), start=1):
            _report(10 + int(80 * idx / total), f"Renderizando stem '{stem_name}'...")

            out_path = os.path.join(output_dir, f"{stem_name}.wav")
            # soundfile espera (samples, channels)
            sf.write(out_path, audio_array.T, samplerate=sample_rate)

            others = [arr for name, arr in stem_arrays.items() if name != stem_name]
            confidence = estimate_stem_confidence(audio_array, mixture_np, others)

            kind = _STEM_NAME_TO_KIND.get(stem_name, StemKind.OTHER)
            duration = audio_array.shape[-1] / sample_rate

            stems.append(
                Stem(
                    kind=kind,
                    file_path=out_path,
                    confidence=confidence,
                    duration_seconds=duration,
                    sample_rate=sample_rate,
                    channels=audio_array.shape[0] if audio_array.ndim > 1 else 1,
                )
            )

        _report(100, "Separação concluída.")
        return stems
