from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_create_dataset_use_case, get_current_principal, get_dataset_repository
from app.application.create_dataset import CreateDataset
from app.domain.enums import DatasetStatus
from app.domain.errors import DatasetInvalidError, DatasetNotFoundError
from app.infrastructure.db.session import get_session
from app.repositories.dataset_repository import DEMO_TENANT_ID, DatasetRepository
from app.schemas.dataset import (
    DatasetResponse,
    PreviewResponse,
    PreviewRow,
    ValidationSummaryResponse,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])

_VALIDATION_CODE_RE = re.compile(r"^V\d{3}$")


def _to_dataset_response(dataset) -> DatasetResponse:
    return DatasetResponse(
        id=dataset.id,
        display_name=dataset.display_name,
        status=dataset.status,
        created_at=dataset.created_at,
    )


@router.post("", status_code=201, response_model=DatasetResponse)
async def create_dataset(
    file: UploadFile = File(...),
    display_name: str | None = Form(default=None),
    use_case: CreateDataset = Depends(get_create_dataset_use_case),
    session: AsyncSession = Depends(get_session),
    principal: str = Depends(get_current_principal),
) -> DatasetResponse:
    raw_bytes = await file.read()
    result = await use_case.execute(
        display_name=display_name or (file.filename or "dataset"),
        raw_bytes=raw_bytes,
        created_by=principal,
    )
    await session.commit()
    return _to_dataset_response(result.dataset)


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    repository: DatasetRepository = Depends(get_dataset_repository),
) -> list[DatasetResponse]:
    datasets = await repository.list_datasets(tenant_id=DEMO_TENANT_ID)
    return [_to_dataset_response(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
    repository: DatasetRepository = Depends(get_dataset_repository),
) -> DatasetResponse:
    dataset = await repository.get_dataset(tenant_id=DEMO_TENANT_ID, dataset_id=dataset_id)
    if dataset is None:
        raise DatasetNotFoundError("Dataset not found.", details={})
    return _to_dataset_response(dataset)


@router.get("/{dataset_id}/validation", response_model=ValidationSummaryResponse)
async def get_validation_summary(
    dataset_id: uuid.UUID,
    repository: DatasetRepository = Depends(get_dataset_repository),
) -> ValidationSummaryResponse:
    dataset = await repository.get_dataset(tenant_id=DEMO_TENANT_ID, dataset_id=dataset_id)
    if dataset is None:
        raise DatasetNotFoundError("Dataset not found.", details={})

    version = await repository.get_latest_version(dataset_id=dataset.id)
    if version is None:
        raise DatasetInvalidError("Dataset has no processed version yet.", details={})

    summary = version.validation_summary
    total_rows = summary["accepted"] + summary["accepted_with_warnings"] + summary["rejected"]

    analysis_blocked = dataset.status in (DatasetStatus.REJECTED, DatasetStatus.CONFLICT)
    analysis_blocked_reason = None
    if dataset.status is DatasetStatus.REJECTED:
        analysis_blocked_reason = summary.get("dataset_rejection_code")
    elif dataset.status is DatasetStatus.CONFLICT:
        analysis_blocked_reason = "V006"

    return ValidationSummaryResponse(
        dataset_id=dataset.id,
        dataset_version_id=version.id,
        accepted=summary["accepted"],
        accepted_with_warnings=summary["accepted_with_warnings"],
        rejected=summary["rejected"],
        total_rows=total_rows,
        dataset_rejection_code=summary.get("dataset_rejection_code"),
        unknown_fields=summary.get("unknown_fields", []),
        conflicting_request_ids=summary.get("conflicting_request_ids", []),
        schema_mapping=version.schema_mapping,
        analysis_blocked=analysis_blocked,
        analysis_blocked_reason=analysis_blocked_reason,
    )


@router.get("/{dataset_id}/preview", response_model=PreviewResponse)
async def get_preview(
    dataset_id: uuid.UUID,
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    repository: DatasetRepository = Depends(get_dataset_repository),
) -> PreviewResponse:
    dataset = await repository.get_dataset(tenant_id=DEMO_TENANT_ID, dataset_id=dataset_id)
    if dataset is None:
        raise DatasetNotFoundError("Dataset not found.", details={})

    version = await repository.get_latest_version(dataset_id=dataset.id)
    if version is None:
        raise DatasetInvalidError("Dataset has no processed version yet.", details={})

    records = await repository.get_records_page(
        dataset_version_id=version.id, cursor=cursor, limit=limit
    )
    def _split_warnings(raw_warnings: list[str]) -> tuple[list[str], str | None]:
        rejection_code = next((w for w in raw_warnings if _VALIDATION_CODE_RE.match(w)), None)
        warnings = [w for w in raw_warnings if w != rejection_code]
        return warnings, rejection_code

    rows = []
    for r in records:
        warnings, rejection_code = _split_warnings(r.warnings)
        rows.append(
            PreviewRow(
                row_number=r.row_number,
                status=r.validation_status,
                masked_text=r.masked_text,
                warnings=warnings,
                rejection_code=rejection_code,
            )
        )
    next_cursor = rows[-1].row_number if len(rows) == limit else None

    return PreviewResponse(dataset_id=dataset.id, rows=rows, cursor=next_cursor, limit=limit)
