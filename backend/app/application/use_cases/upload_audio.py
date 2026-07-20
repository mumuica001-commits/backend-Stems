import os
import shutil
import uuid
from fastapi import UploadFile

from app.core.config import get_settings
from app.domain.entities import SeparationJob, SeparationEngine
from app.infrastructure.queue.job_queue import JobQueue
from app.infrastructure.storage.job_repository import JobRepository


class UploadAudioUseCase:
    def __init__(
        self,
        job_repository: JobRepository | None = None,
        job_queue: JobQueue | None = None,
    ):
        self._jobs = job_repository or JobRepository()
        self._queue = job_queue or JobQueue()
        self._settings = get_settings()

    async def execute(self, file: UploadFile, engine: str = "demucs") -> SeparationJob:
        job_id = str(uuid.uuid4())
        
        # Garante a criação da pasta temporária no container
        upload_dir = os.path.join(self._settings.storage_root, self._settings.uploads_dir)
        os.makedirs(upload_dir, exist_ok=True)

        file_extension = os.path.splitext(file.filename or "")[1] or ".mp3"
        source_path = os.path.join(upload_dir, f"{job_id}{file_extension}")

        # Salva o arquivo enviado no disco do container
        with open(source_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Converte a string do engine para o Enum
        try:
            selected_engine = SeparationEngine(engine.lower())
        except ValueError:
            selected_engine = SeparationEngine.DEMUCS

        # Cria a entidade do Job
        job = SeparationJob(
            id=job_id,
            filename=file.filename or "audio.mp3",
            source_path=source_path,
            engine=selected_engine,
        )

        # Salva o job no repositório (Redis)
        self._jobs.save(job)

        # Envia para a fila do RQ
        self._queue.enqueue_processing(job.id)

        return job