from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportResponse(BaseModel):
    report_id: UUID
    run_id: UUID
    status: str
    format: str
    checksum: str | None
    generated_at: datetime | None
    safe_error: str | None
