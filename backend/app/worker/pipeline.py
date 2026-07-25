"""Job claim-and-execute loop (docs/12-backend.md section 5).

`run_once` claims at most one pending job via `SELECT ... FOR UPDATE SKIP
LOCKED` and executes the whole run pipeline for it. Kept side-effect-testable
separately from the infinite loop in `app/worker/main.py`.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.execute_analysis_run import ExecuteAnalysisRun
from app.config import get_settings
from app.domain.enums import RunStatus
from app.infrastructure.providers.factory import build_llm_provider
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.best_practice_repository import BestPracticeRepository
from app.services.best_practice_detection import BestPracticeDetectionService

logger = logging.getLogger("arvexo.worker")


async def run_once(session: AsyncSession, *, worker_id: str) -> bool:
    """Returns True if a job was claimed and processed (successfully or not)."""

    repo = AnalysisRepository(session)
    job = await repo.claim_next_job(worker_id=worker_id)
    if job is None:
        return False

    settings = get_settings()
    llm_provider = build_llm_provider(settings)
    best_practice_detector = BestPracticeDetectionService(BestPracticeRepository(session))
    executor = ExecuteAnalysisRun(
        repo,
        llm_provider,
        best_practice_detector,
        max_scenario_samples=settings.llm_max_samples,
        max_recommendations=settings.llm_max_recommendations,
    )

    try:
        await executor.execute(job.run_id)
        await repo.complete_job(job)
    except Exception:
        logger.exception("job failed run_id=%s job_id=%s", job.run_id, job.id)
        await repo.complete_job(job, safe_error="PIPELINE_EXECUTION_FAILED")
        run = await repo.get_run_by_id(job.run_id)
        if run is not None:
            run.status = RunStatus.FAILED
            run.error_code = "PIPELINE_EXECUTION_FAILED"

    await session.commit()
    return True
