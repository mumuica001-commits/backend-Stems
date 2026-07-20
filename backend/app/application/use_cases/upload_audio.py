import os
import shutil
import uuid
from typing import Optional
from fastapi import UploadFile

from app.core.config import get_settings
from app.domain.entities import SeparationJob
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

    async def execute(
        self, 
        file: UploadFile, 
        filename: Optional[str] = None, 
        engine: str = "demucs"
    ) -> SeparationJob:
        job_id = str(uuid.uuid4())
        
        # Nome final do arquivo
        final_filename = filename or file.filename or "audio.mp3"
        
        # Garante a criação da pasta temporária no container
        upload_dir = os.path.join(self._settings.storage_root, self._settings.uploads_dir)
        os.makedirs(upload_dir, exist_ok=True)

        file_extension = os.path.splitext(final_filename)[1] or ".mp3"
        source_path = os.path.join(upload_dir, f"{job_id}{file_extension}")

        # Salva o arquivo enviado no disco do container
        with open(source_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        selected_engine = engine.lower() if isinstance(engine, str) else engine

        # Cria a entidade do Job
        job = SeparationJob(
            id=job_id,
            filename=final_filename,
            source_path=source_path,
            engine=selected_engine,
        )

        # Salva o job no repositório (Redis)
        self._jobs.save(job)

        # Envia para a fila do RQ
        self._queue.enqueue_processing(job.id)

        return job