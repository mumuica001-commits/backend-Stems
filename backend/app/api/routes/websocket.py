from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.exceptions import JobNotFoundError
from app.infrastructure.storage.job_repository import JobRepository
from app.infrastructure.websocket.progress_broadcaster import ProgressSubscriber

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    settings = get_settings()

    try:
        job = JobRepository().get(job_id)
    except JobNotFoundError:
        await websocket.send_json({"error": "job não encontrado"})
        await websocket.close()
        return

    # envia estado atual imediatamente (cliente pode conectar após progresso já ter avançado)
    await websocket.send_json(
        {
            "job_id": job.id,
            "status": job.status.value,
            "percent": job.progress_percent,
            "message": job.stage_message,
        }
    )

    if job.status.value in ("completed", "failed"):
        await websocket.close()
        return

    subscriber = ProgressSubscriber()

    async def _heartbeat():
        while True:
            await asyncio.sleep(settings.ws_heartbeat_seconds)
            await websocket.send_json({"type": "heartbeat"})

    heartbeat_task = asyncio.create_task(_heartbeat())

    try:
        async for update in subscriber.listen(job_id):
            await websocket.send_json(update)
            if update.get("status") in ("completed", "failed"):
                break
    except WebSocketDisconnect:
        logger.info("Cliente desconectou do progresso do job %s", job_id)
    finally:
        heartbeat_task.cancel()
        await websocket.close()
