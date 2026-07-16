from __future__ import annotations

from app.domain.entities import SeparationEngineName
from app.domain.exceptions import SeparationEngineError
from app.infrastructure.separation.base import SeparationEngine
from app.infrastructure.separation.demucs_engine import DemucsEngine
from app.infrastructure.separation.dsp_mock_engine import DSPMockEngine
from app.infrastructure.separation.mdx_engine import MDXNetEngine


class SeparationEngineFactory:
    """
    Ponto único de criação de engines. Adicionar um novo modelo
    (SCNet, Bandit, Open-Unmix...) = implementar SeparationEngine
    + registrar aqui. Nenhum outro lugar do sistema muda.
    """

    _DEMUCS_MODELS = {
        SeparationEngineName.DEMUCS_HTDEMUCS_6S: "htdemucs_6s",
        SeparationEngineName.DEMUCS_HTDEMUCS_FT: "htdemucs_ft",
    }
    _MDX_MODELS = {
        SeparationEngineName.MDX_NET_KARAOKE_2: "mdx_net_karaoke_2",
        SeparationEngineName.MDX23C: "mdx23c",
    }

    @classmethod
    def create(cls, engine_name: SeparationEngineName) -> SeparationEngine:
        if engine_name == SeparationEngineName.DEV_DSP_MOCK:
            return DSPMockEngine()
        if engine_name in cls._DEMUCS_MODELS:
            return DemucsEngine(model_name=cls._DEMUCS_MODELS[engine_name])
        if engine_name in cls._MDX_MODELS:
            return MDXNetEngine(model_key=cls._MDX_MODELS[engine_name])
        raise SeparationEngineError(str(engine_name), "engine não registrado na factory")

    @classmethod
    def list_available(cls) -> list[dict]:
        """Usado pelo endpoint GET /engines — reporta o que está de fato pronto pra uso."""
        result = []
        for engine_name in SeparationEngineName:
            try:
                engine = cls.create(engine_name)
                result.append(
                    {
                        "id": engine_name.value,
                        "name": engine.name,
                        "supported_stems": engine.supported_stems,
                        "available": engine.is_available(),
                    }
                )
            except SeparationEngineError:
                result.append({"id": engine_name.value, "available": False})
        return result
