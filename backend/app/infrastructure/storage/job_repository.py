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
                self._redis = redis.Redis.from_url(raw_url, ssl_cert_reqs="none", decode_responses=True)
            else:
                self._redis = redis.Redis.from_url(raw_url, decode_responses=True)
        else:
            self._redis = redis_client

    def get_by_id(self, job_id: str) -> Optional[Any]:
        data = self._redis.get(f"job:{job_id}")
        if data:
            try:
                from app.domain.entities import SeparationJob, JobStatus, SeparationEngine
                raw = json.loads(data)
                
                job = SeparationJob(
                    id=raw.get("id"),
                    filename=raw.get("filename", "audio.mp3"),
                    source_path=raw.get("source_path", ""),
                    engine=SeparationEngine(raw.get("engine", "demucs")),
                    status=JobStatus(raw.get("status", "pending")),
                    progress_percent=float(raw.get("progress_percent", 0.0)),
                    stage_message=raw.get("stage_message", "")
                )
                return job
            except Exception:
                return None
        return None

    def save(self, job: Any) -> Any:
        job_id = getattr(job, 'id', None)
        if not job_id:
            job_id = str(uuid.uuid4())
            if hasattr(job, 'id'):
                job.id = job_id

        # Serializa as propriedades básicas do job para JSON
        job_data = {
            "id": getattr(job, "id", job_id),
            "filename": getattr(job, "filename", ""),
            "source_path": getattr(job, "source_path", ""),
            "engine": getattr(job.engine, "value", str(job.engine)) if hasattr(job, "engine") else "demucs",
            "status": getattr(job.status, "value", str(job.status)) if hasattr(job, "status") else "pending",
            "progress_percent": getattr(job, "progress_percent", 0.0),
            "stage_message": getattr(job, "stage_message", "")
        }

        self._redis.set(f"job:{job_id}", json.dumps(job_data), ex=86400)
        return job