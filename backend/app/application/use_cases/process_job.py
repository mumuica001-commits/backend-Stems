from __future__ import annotations

import os

from app.application.services.analysis_service import AnalysisService
from app.application.services.separation_service import SeparationService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.entities import JobStatus, SeparationJob
from app.infrastructure.separation.base import SeparationProgress
from app.infrastructure.storage.job_repository import JobRepository
from app.infrastructure.websocket.progress_broadcaster import ProgressPublisher

logger = get_logger(__name__)


class ProcessJobUseCase:
    """
    Executado dentro do worker (RQ). Roda a pipeline completa:
      1. Análise musical (BPM, key, chords, loudness) — sobre o áudio original
      2. Separação de stems com o engine escolhido
      3. Persiste resultado e publica progresso em cada etapa
    """

    def __init__(
        self,
        job_repository: JobRepository | None = None,
        separation_service: SeparationService | None = None,
        analysis_service: AnalysisService | None = None,
        publisher: ProgressPublisher | None = None,
    ):
        self._jobs = job_repository or JobRepository()
        self._separation = separation_service or SeparationService()
        self._analysis = analysis_service or AnalysisService()
        self._publisher = publisher or ProgressPublisher()
        self._settings = get_settings()

    def execute(self, job_id: str) -> None:
        job = self._jobs.get(job_id)

        try:
            self._run_analysis(job)
            self._run_separation(job)
            job.mark_completed()
            self._save_and_publish(job, "Processamento concluído.")
        except Exception as exc:
            logger.exception("Job %s falhou", job_id)
            job.mark_failed(str(exc))
            self._save_and_publish(job, f"Erro: {exc}")
            raise

    def _run_analysis(self, job: SeparationJob) -> None:
        job.mark_progress(JobStatus.ANALYZING, 5, "Analisando BPM, tonalidade e acordes...")
        self._save_and_publish(job, job.stage_message)

        job.analysis = self._analysis.analyze(job.source_path)

        job.mark_progress(JobStatus.ANALYZING, 20, "Análise musical concluída.")
        self._save_and_publish(job, job.stage_message)

    def _run_separation(self, job: SeparationJob) -> None:
        job.mark_progress(JobStatus.SEPARATING, 25, f"Separando stems com {job.engine.value}...")
        self._save_and_publish(job, job.stage_message)

        output_dir = os.path.join(self._settings.storage_root, self._settings.results_dir, job.id)

        def on_progress(progress: SeparationProgress) -> None:
            # mapeia 0-100 da separação para a faixa 25-95 do job total
            overall_percent = 25 + (progress.percent * 0.70)
            job.mark_progress(JobStatus.SEPARATING, overall_percent, progress.message)
            self._save_and_publish(job, progress.message)

        job.stems = self._separation.separate(
            input_path=job.source_path,
            output_dir=output_dir,
            engine_name=job.engine,
            on_progress=on_progress,
        )

        job.mark_progress(JobStatus.POST_PROCESSING, 95, "Finalizando...")
        self._save_and_publish(job, job.stage_message)

    def _save_and_publish(self, job: SeparationJob, message: str) -> None:
        self._jobs.save(job)
        self._publisher.publish(job.id, job.status.value, job.progress_percent, message)
