from __future__ import annotations

import os
import redis
from rq import Queue

from app.core.config import get_settings


class JobQueue:
    """Fina camada sobre RQ — escolhida por ser simples de operar (vs Celery)
    para uma fila de jobs longos e sequenciais como separação de áudio."""

    def __init__(self, redis_client: redis.Redis | None = None):
        settings = get_settings()
        
        if not redis_client:
            raw_url = (
                os.getenv("redis_url") or 
                os.getenv("REDIS_URL") or 
                settings.redis_url
            )
            
            # ATENÇÃO: Se a URL começar com rediss:// (produção no Railway), 
            # mantemos o rediss:// original e deixamos a biblioteca gerenciar o SSL nativamente.
            if raw_url.startswith("rediss://"):
                self._redis = redis.Redis.from_url(
                    raw_url,
                    ssl_cert_reqs="none", # Na versão 5.x, se passado, precisa ser a string "none" minúscula, ou simplesmente omitido
                    socket_timeout=5.0,
                    retry_on_timeout=False
                )
            else:
                # Conexão padrão local (sem SSL)
                self._redis = redis.Redis.from_url(
                    raw_url,
                    socket_timeout=5.0,
                    retry_on_timeout=False
                )

            self._redis = redis.Redis.from_url(
                redis_url, 
                ssl_cert_reqs=None,
                socket_timeout=5.0,
                retry_on_timeout=False
            )
        else:
            self._redis = redis_client

        self._queue = Queue(settings.queue_name, connection=self._redis, default_timeout="30m")

    def enqueue_processing(self, job_id: str):
        from app.infrastructure.queue.tasks import process_separation_job
        from fastapi import HTTPException

        print(f"[DEBUG REDIS] Tentando conectar no Redis...")
        
        try:
            self._redis.ping()
            print("[DEBUG REDIS] Conexão com Redis realizada com SUCESSO!")
            return self._queue.enqueue(process_separation_job, job_id, job_id=job_id)
            
        except Exception as e:
            print(f"[DEBUG REDIS ERRO CRÍTICO] Falha ao interagir com o Redis: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Erro de comunicação com a fila de processamento (Redis). Causa: {str(e)}"
            )

    def get_queue_position(self, job_id: str) -> int | None:
        job_ids = self._queue.job_ids
        return job_ids.index(job_id) if job_id in job_ids else None
    
    #Forçando commit
    