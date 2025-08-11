from __future__ import annotations

import os
import signal
import sys
from typing import List

import logging
from rq import Worker
try:
    from rq import SimpleWorker  # type: ignore
except Exception:  # pragma: no cover
    SimpleWorker = None  # type: ignore

from .queue import get_redis_and_queue


def main(argv: List[str] | None = None) -> int:
    """
    // AICODE-NOTE: Точка входа RQ-воркера.
    Использует Redis из `REDIS_URL` и очередь из `AGENT_QUEUE`.
    Запускает `rq.Worker` и блокируется до SIGINT/SIGTERM.
    """
    _argv = argv if argv is not None else sys.argv[1:]

    logging.basicConfig(level=os.getenv("AGENT_WORKER_LOG_LEVEL", "INFO"))
    redis, queue = get_redis_and_queue()

    simple = os.getenv("AGENT_WORKER_SIMPLE", "0") in {"1", "true", "True"}
    if simple and SimpleWorker is not None:
        worker = SimpleWorker([queue], connection=redis)  # type: ignore[assignment]
        worker.log.info("Starting SimpleWorker (no forking) on queue '%s'", queue.name)
    else:
        worker = Worker([queue], connection=redis)
        worker.log.info("Starting Worker (forking) on queue '%s'", queue.name)

    # Грейсфул остановка по SIGTERM/SIGINT
    def _graceful_stop(signum, frame):  # type: ignore[no-untyped-def]
        try:
            worker.log.info("Received signal %s, stopping worker...", signum)
        except Exception:
            pass
        worker.stop()

    signal.signal(signal.SIGINT, _graceful_stop)
    signal.signal(signal.SIGTERM, _graceful_stop)

    worker.work(with_scheduler=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


