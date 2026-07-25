from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import BestPracticeStatus


class BestPracticeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | str
    title: str
    short_description: str
    department: str = "Не определено"
    department_origin: str | None = None
    scenario: str = "Не определено"
    scenario_id: UUID | str | None = None
    created_at: datetime
    detected_at: datetime
    status: BestPracticeStatus
    confidence_score: float
    impact_score: float
    adoption_count: int
    estimated_time_saved: float
    estimated_fte_saved: float
    estimated_money_saved: float = 0
    tags: list[str]
    recommendation: str = "Требуется экспертная проверка перед распространением."
    user_count: int
    usage_count: int
    average_rating: float | None = None
    success_rate: float = 0
    error_rate: float = 0
    growth_rate: float = 0
    departments: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    detection_evidence: dict = Field(default_factory=dict)
    published_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    recommended_departments: list[str] = Field(default_factory=list)
    is_estimated: bool = True

    @model_validator(mode="before")
    @classmethod
    def normalize_enterprise_fields(cls, value):
        if isinstance(value, dict):
            data = dict(value)
            data.setdefault("department", data.get("department_origin", "Не определено"))
            data.setdefault("department_origin", data.get("department"))
            data.setdefault("scenario", data.get("title", "Не определено"))
            data.setdefault("scenario_id", data.get("source_scenario_id"))
            data.setdefault("recommendation", "Требуется экспертная проверка перед распространением.")
            data.setdefault("departments", [data["department"]])
            data.setdefault("models", [])
            data.setdefault("published_at", None)
            return data
        return value


class BestPracticeListResponse(BaseModel):
    items: list[BestPracticeResponse]
    total: int
    offset: int
    limit: int


class BestPracticeTopResponse(BaseModel):
    new: list[BestPracticeResponse]
    fast_growing: list[BestPracticeResponse]
    most_effective: list[BestPracticeResponse]
    by_department: dict[str, list[BestPracticeResponse]]
    by_model: dict[str, list[BestPracticeResponse]]
