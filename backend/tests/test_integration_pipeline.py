"""
Teste de integração de ponta a ponta — reproduz em CI o mesmo teste manual
que validamos rodando a API e o worker de verdade: gera um áudio sintético,
roda a pipeline completa (análise + separação com o engine dev_dsp_mock,
que não depende de pesos de IA) e verifica que o resultado é coerente.

Requer um Redis rodando (ver .github/workflows/backend-ci.yml e/ou
`redis-server` local). O job é processado SINCRONAMENTE aqui (chamando
ProcessJobUseCase diretamente) em vez de via worker RQ real, pra não
depender de subir um processo separado só pra rodar o teste — mas exercita
exatamente o mesmo código que o worker de produção roda.
"""
from __future__ import annotations

import os
import shutil
import uuid

import numpy as np
import pytest
import redis
import soundfile as sf

from app.application.use_cases.process_job import ProcessJobUseCase
from app.domain.entities import JobStatus, SeparationEngineName, SeparationJob
from app.infrastructure.storage.job_repository import JobRepository
from app.infrastructure.websocket.progress_broadcaster import ProgressPublisher


def _redis_available() -> bool:
    try:
        client = redis.Redis.from_url("redis://localhost:6379/0")
        return client.ping()
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _redis_available(), reason="Redis não disponível — suba com `redis-server` para rodar este teste."
)


@pytest.fixture
def synthetic_song(tmp_path) -> str:
    """Áudio estéreo sintético com um acorde de Lá maior (A-C#-E) + clique percussivo."""
    sr = 22050
    duration = 4.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    chord = (
        0.2 * np.sin(2 * np.pi * 220.0 * t)
        + 0.15 * np.sin(2 * np.pi * 277.18 * t)
        + 0.15 * np.sin(2 * np.pi * 329.63 * t)
    )
    click_env = (np.mod(t, 0.5) < 0.02).astype(np.float32)
    percussive = click_env * np.random.default_rng(0).standard_normal(len(t)) * 0.3

    mono = chord + percussive
    left = mono + 0.05 * np.sin(2 * np.pi * 5 * t)
    right = mono - 0.05 * np.sin(2 * np.pi * 5 * t)
    stereo = np.stack([left, right]).T.astype(np.float32)

    path = tmp_path / "synthetic_song.wav"
    sf.write(str(path), stereo, sr)
    return str(path)


@pytest.fixture
def storage_dir(tmp_path):
    output_dir = tmp_path / "job_output"
    yield str(output_dir)
    shutil.rmtree(str(output_dir), ignore_errors=True)


def test_full_pipeline_analysis_and_separation(synthetic_song, storage_dir):
    job_repo = JobRepository()
    job = SeparationJob(
        id=str(uuid.uuid4()),
        original_filename="synthetic_song.wav",
        source_path=synthetic_song,
        engine=SeparationEngineName.DEV_DSP_MOCK,
    )
    job_repo.save(job)

    # roda a MESMA lógica que o worker de produção executa, só que
    # sincronamente (sem passar pela fila RQ) para o teste ser determinístico
    os.environ.setdefault("STEMSAI_STORAGE_ROOT", str(storage_dir))
    use_case = ProcessJobUseCase(job_repository=job_repo, publisher=ProgressPublisher())
    use_case.execute(job.id)

    result = job_repo.get(job.id)

    assert result.status == JobStatus.COMPLETED
    assert result.error_message is None

    # 6 stems reais, todos com arquivo no disco
    assert len(result.stems) == 6
    for stem in result.stems:
        assert os.path.isfile(stem.file_path), f"arquivo do stem '{stem.kind}' não foi criado"
        assert 0.0 <= stem.confidence <= 1.0

    # análise musical deve ter detectado o acorde de A major que sintetizamos
    assert result.analysis is not None
    assert result.analysis.key is not None
    assert "A" in result.analysis.key  # A major ou A minor — a tríade é inequívoca (A-C#-E = A major)
    assert result.analysis.bpm is not None
    assert result.analysis.lufs_integrated is not None
    assert result.analysis.duration_seconds == pytest.approx(4.0, abs=0.05)
