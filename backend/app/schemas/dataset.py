from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DatasetResponse(BaseModel):
    id: UUID
    display_name: str
    status: str
    created_at: datetime


class ValidationSummaryResponse(BaseModel):
    dataset_id: UUID
    dataset_version_id: UUID
    accepted: int
    accepted_with_warnings: int
    rejected: int
    total_rows: int
    dataset_rejection_code: str | None
    unknown_fields: list[str]
    conflicting_request_ids: list[str]
    schema_mapping: dict[str, str]
    analysis_blocked: bool
    analysis_blocked_reason: str | None


class PreviewRow(BaseModel):
    row_number: int
    status: str
    masked_text: str | None
    warnings: list[str]
    rejection_code: str | None


class PreviewResponse(BaseModel):
    dataset_id: UUID
    rows: list[PreviewRow]
    cursor: int | None
    limit: int
