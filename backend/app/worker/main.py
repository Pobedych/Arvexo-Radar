"""Worker process entrypoint: polls `analysis_jobs` and executes the run
pipeline for whatever job it claims (docs/12-backend.md section 5).
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid

from app.infrastructure.db.session import AsyncSessionLocal
from app.worker.pipeline import run_once

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arvexo.worker")

POLL_INTERVAL_SECONDS = 2.0
IDLE_POLL_INTERVAL_SECONDS = 5.0
WORKER_ID = f"worker-{os.getpid()}-{uuid.uuid4().hex[:8]}"


async def main() -> None:
    logger.info("worker started id=%s", WORKER_ID)
    while True:
        async with AsyncSessionLocal() as session:
            processed = await run_once(session, worker_id=WORKER_ID)
        await asyncio.sleep(POLL_INTERVAL_SECONDS if processed else IDLE_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
