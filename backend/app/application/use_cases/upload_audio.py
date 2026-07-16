from __future__ import annotations

import os
import shutil

from app.core.config import get_settings
from app.domain.entities import SeparationEngineName, SeparationJob
from app.domain.exceptions import AudioTooLargeError, UnsupportedAudioFormatError
from app.infrastructure.queue.job_queue import JobQueue
from app.infrastructure.storage.job_repository import JobRepository


class UploadAudioUseCase:
    def __init__(self, job_repository: JobRepository | None = None, job_queue: JobQueue | None = None):
        self._jobs = job_repository or JobRepository()
        self._queue = job_queue or JobQueue()
        self._settings = get_settings()

    def execute(
        self,
        filename: str,
        file_stream,
        content_length_bytes: int,
        engine: SeparationEngineName,
    ) -> SeparationJob:
        self._validate(filename, content_length_bytes)

        job = SeparationJob(original_filename=filename, engine=engine)

        uploads_dir = os.path.join(self._settings.storage_root, self._settings.uploads_dir)
        os.makedirs(uploads_dir, exist_ok=True)

        extension = os.path.splitext(filename)[1].lower()
        dest_path = os.path.join(uploads_dir, f"{job.id}{extension}")
        with open(dest_path, "wb") as dest_file:
            shutil.copyfileobj(file_stream, dest_file)

        job.source_path = dest_path
        self._jobs.save(job)
        self._queue.enqueue_processing(job.id)

        return job

    def _validate(self, filename: str, content_length_bytes: int) -> None:
        extension = os.path.splitext(filename)[1].lower()
        if extension not in self._settings.allowed_extensions:
            raise UnsupportedAudioFormatError(extension)

        size_mb = content_length_bytes / (1024 * 1024)
        if size_mb > self._settings.max_upload_size_mb:
            raise AudioTooLargeError(size_mb, self._settings.max_upload_size_mb)
