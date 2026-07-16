from __future__ import annotations

from app.core.logging import get_logger
from app.domain.entities import SeparationEngineName, Stem
from app.infrastructure.separation.base import ProgressCallback
from app.infrastructure.separation.engine_factory import SeparationEngineFactory

logger = get_logger(__name__)


class SeparationService:
    """Camada fina sobre a factory — ponto único de entrada para separar áudio."""

    def separate(
        self,
        input_path: str,
        output_dir: str,
        engine_name: SeparationEngineName,
        on_progress: ProgressCallback | None = None,
    ) -> list[Stem]:
        engine = SeparationEngineFactory.create(engine_name)

        if not engine.is_available():
            raise RuntimeError(
                f"Engine '{engine_name.value}' não está disponível "
                f"(dependências ou pesos do modelo ausentes)."
            )

        logger.info("Iniciando separação com engine=%s input=%s", engine.name, input_path)
        return engine.separate(input_path, output_dir, on_progress=on_progress)
