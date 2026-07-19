from __future__ import annotations

import os  # Adicionado para ler o ambiente diretamente
import redis
from rq import Queue

from app.core.config import get_settings


class JobQueue:
    """Fina camada sobre RQ — escolhida por ser simples de operar (vs Celery)
    para uma fila de jobs longos e sequenciais como separação de áudio."""

    def __init__(self, redis_client: redis.Redis | None = None):
        settings = get_settings()
        
        # Se o cliente não for passado, buscamos a URL com fallbacks seguros para o Railway
        if not redis_client:
            # Tenta pegar da variável minúscula, se não tiver tenta a maiúscula, se não tiver usa o config
            redis_url = (
                os.getenv("redis_url") or 
                os.getenv("REDIS_URL") or 
                settings.redis_url
            )
            self._redis = redis.Redis.from_url(redis_url)
        else:
            self._redis = redis_client

        self._queue = Queue(settings.queue_name, connection=self._redis, default_timeout="30m")

    def enqueue_processing(self, job_id: str):
        from app.infrastructure.queue.tasks import process_separation_job

        return self._queue.enqueue(process_separation_job, job_id, job_id=job_id)

    def get_queue_position(self, job_id: str) -> int | None:
        job_ids = self._queue.job_ids
        return job_ids.index(job_id) if job_id in job_ids else None