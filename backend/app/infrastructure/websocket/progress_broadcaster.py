"""
Broadcaster de progresso de jobs.

O worker (processo separado da API) publica atualizações num canal
Redis Pub/Sub por job. A API assina esse canal quando um cliente
WebSocket se conecta e repassa as mensagens em tempo real.

Isso permite escalar workers horizontalmente sem acoplar progresso
a estado em memória de um único processo FastAPI.
"""
from __future__ import annotations

import json

import redis
import redis.asyncio as aioredis

from app.core.config import get_settings

_CHANNEL_PREFIX = "stemsai:progress:"


def channel_for_job(job_id: str) -> str:
    return f"{_CHANNEL_PREFIX}{job_id}"


class ProgressPublisher:
    """Usado pelo worker (síncrono) para publicar updates."""

    def __init__(self, redis_client: redis.Redis | None = None):
        settings = get_settings()
        self._redis = redis_client or redis.Redis.from_url(settings.redis_url)

    def publish(self, job_id: str, status: str, percent: float, message: str) -> None:
        payload = json.dumps({"job_id": job_id, "status": status, "percent": percent, "message": message})
        self._redis.publish(channel_for_job(job_id), payload)


class ProgressSubscriber:
    """Usado pela API (assíncrono) para repassar updates ao WebSocket do cliente."""

    def __init__(self):
        settings = get_settings()
        self._redis = aioredis.from_url(settings.redis_url)

    async def listen(self, job_id: str):
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel_for_job(job_id))
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                yield json.loads(message["data"])
        finally:
            await pubsub.unsubscribe(channel_for_job(job_id))
            await pubsub.close()
