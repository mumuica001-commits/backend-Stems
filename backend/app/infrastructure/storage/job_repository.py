import uuid
from typing import Dict, Any, Optional

# Repositório totalmente simulado em memória (blindado contra erros de importação)
class JobRepository:
    _db: Dict[str, Any] = {}

    async def get_by_id(self, job_id: str) -> Optional[Any]:
        return self._db.get(job_id)

    async def save(self, job: Any) -> Any:
        # Se o objeto tiver um atributo id, usamos ou criamos ele
        if hasattr(job, 'id'):
            if not job.id:
                job.id = str(uuid.uuid4())
            self._db[job.id] = job
        # Se for um dicionário
        elif isinstance(job, dict):
            if 'id' not in job or not job['id']:
                job['id'] = str(uuid.uuid4())
            self._db[job['id']] = job
        else:
            # Fallback genérico para salvar de qualquer forma
            job_id = str(uuid.uuid4())
            self._db[job_id] = job
        return job