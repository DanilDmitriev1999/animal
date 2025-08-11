from __future__ import annotations

import os
from typing import Tuple

from redis import Redis
from rq import Queue


def get_redis_and_queue() -> Tuple[Redis, Queue]:
    """
    // AICODE-NOTE: Возвращает клиент Redis и очередь RQ.
    Источник конфигурации: `REDIS_URL`, `AGENT_QUEUE`.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    queue_name = os.getenv("AGENT_QUEUE", "agents")
    redis_client = Redis.from_url(redis_url)
    return redis_client, Queue(name=queue_name, connection=redis_client)


