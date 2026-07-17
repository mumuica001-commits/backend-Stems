import uuid
from typing import Dict, Optional
from app.domain.entities import Job

# Repositório simulado em memória para o seu projeto não dar erro
class JobRepository:
    _db: Dict[str, Job] = {}

    async def get_by_id(self, job_id: str) -> Optional[Job]:
        return self._db.get(job_id)

    async def save(self, job: Job) -> Job:
        if not job.id:
            job.id = str(uuid.uuid4())
        self._db[job.id] = job
        return job