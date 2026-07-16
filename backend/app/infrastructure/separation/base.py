"""
Contrato que todo engine de separação de fonte deve cumprir.

Isso é o que permite trocar Demucs <-> MDX-Net <-> (futuro) SCNet/Bandit
sem tocar em nenhuma linha do resto do sistema — Strategy Pattern clássico.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from app.domain.entities import Stem


@dataclass
class SeparationProgress:
    percent: float          # 0..100 dentro da etapa de separação
    message: str


ProgressCallback = Callable[[SeparationProgress], None]


class SeparationEngine(ABC):
    """
    Cada implementação concreta encapsula um modelo de IA de separação.
    Deve ser determinística o suficiente para permitir cache de resultado.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def supported_stems(self) -> list[str]:
        """Stems que este engine é capaz de produzir."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se pesos/dependências do modelo estão presentes."""
        ...

    @abstractmethod
    def separate(
        self,
        input_path: str,
        output_dir: str,
        on_progress: ProgressCallback | None = None,
    ) -> list[Stem]:
        """
        Executa a separação e retorna os Stems gerados, já com
        confidence estimada (ver EngineConfidenceEstimator).
        """
        ...
