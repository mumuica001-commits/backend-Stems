import json
import uuid
import os
import redis
from typing import Any, Optional
from app.core.config import get_settings

class JobRepository:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        if not redis_client:
            settings = get_settings()
            raw_url = os.getenv("redis_url") or os.getenv("REDIS_URL") or settings.redis_url
            
            if raw_url.startswith("rediss://"):
                self._redis = redis.Redis.from_url(raw_url, ssl_cert_reqs="none")
            else:
                self._redis = redis.Redis.from_url(raw_url)
        else:
            self._redis = redis_client

    def get_by_id(self, job_id: str) -> Optional[Any]:
        # Busca os dados do Job diretamente do Redis
        data = self._redis.get(f"job:{job_id}")
        if data:
            # Recompoe/Desserializa o objeto se necessário
            return data
        return None

    def save(self, job: Any) -> Any:
        job_id = getattr(job, 'id', None) or (job.get('id') if isinstance(job, dict) else None)
        if not job_id:
            job_id = str(uuid.uuid4())
            if hasattr(job, 'id'):
                job.id = job_id
            elif isinstance(job, dict):
                job['id'] = job_id

        # Salva o estado do Job no Redis por até 24h
        # (Se 'job' for uma entidade complexa, converta para dict/json ou pickle)
        self._redis.set(f"job:{job_id}", str(job), ex=86400)
        return job