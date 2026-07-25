"""CreateAnalysisRun use case (docs/12-backend.md section 3,
docs/09-architecture.md section 7).

Only enqueues: creates the immutable run + its first job row and returns
`queued`. The worker (app/worker/pipeline.py) claims the job and executes
the actual pipeline stages, matching the documented `queued -> ... ->
completed` state model.
"""

from __future__ import annotations

import uuid

from app.domain.enums import RunStage
from app.domain.errors import DatasetInvalidError, DatasetNotFoundError
from app.infrastructure.db.models import AnalysisRun
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.dataset_repository import DatasetRepository

TAXONOMY_VERSION = "taxonomy-v1"


class CreateAnalysisRunResult:
    def __init__(self, run: AnalysisRun, reused_existing: bool) -> None:
        self.run = run
        self.reused_existing = reused_existing


class CreateAnalysisRun:
    def __init__(
        self,
        dataset_repository: DatasetRepository,
        analysis_repository: AnalysisRepository,
    ) -> None:
        self._datasets = dataset_repository
        self._analysis = analysis_repository

    async def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        dataset_id: uuid.UUID,
        provider_mode: str,
        locale: str,
        created_by: str,
        idempotency_key: str | None,
    ) -> CreateAnalysisRunResult:
        dataset = await self._datasets.get_dataset(tenant_id=tenant_id, dataset_id=dataset_id)
        if dataset is None:
            raise DatasetNotFoundError("Dataset not found.", details={})

        version = await self._datasets.get_latest_version(dataset_id=dataset.id)
        if version is None:
            raise DatasetInvalidError("Dataset has no processed version yet.", details={})

        if dataset.status not in ("validated",):
            raise DatasetInvalidError(
                "Dataset is not in a state that allows analysis.",
                details={"dataset_status": dataset.status},
            )

        if idempotency_key:
            existing = await self._analysis.find_run_by_idempotency_key(version.id, idempotency_key)
            if existing is not None:
                return CreateAnalysisRunResult(existing, reused_existing=True)

        config_snapshot = {
            "provider_mode": provider_mode,
            "taxonomy_version": TAXONOMY_VERSION,
            "locale": locale,
        }

        run = await self._analysis.create_run(
            tenant_id=tenant_id,
            dataset_version_id=version.id,
            config_snapshot=config_snapshot,
            created_by=created_by,
            idempotency_key=idempotency_key,
        )
        await self._analysis.create_job(run_id=run.id, stage=RunStage.EMBEDDING)

        return CreateAnalysisRunResult(run, reused_existing=False)
