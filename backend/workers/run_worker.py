"""
Processo worker — consome a fila `stemsai:separation` e executa
ProcessJobUseCase para cada job. Rode em réplicas separadas do
processo da API para escalar processamento independentemente
(inclusive com réplicas GPU vs CPU).

Uso:
    python workers/run_worker.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import redis
from rq import Worker

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    redis_conn = redis.Redis.from_url(settings.redis_url)
    worker = Worker([settings.queue_name], connection=redis_conn)

    logger.info("Worker iniciado. Ouvindo fila '%s'...", settings.queue_name)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
