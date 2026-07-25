from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

DataStatus = Literal["actual", "estimate", "mixed", "demo"]


class PeriodResponse(BaseModel):
    date_from: datetime
    date_to: datetime
    label: str


class DataProvenance(BaseModel):
    data_mode: Literal["live", "demo", "mixed"] = "demo"
    data_status: DataStatus = "demo"
    estimated_share: float = Field(ge=0, le=1)
    source: str
    limitations: list[str] = []


class KpiValue(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    change_percent: float | None = None
    data_status: DataStatus
    formula: str
    source: str
    assumption: str | None = None


class OverviewEnterpriseResponse(BaseModel):
    period: PeriodResponse
    provenance: DataProvenance
    usage_and_cost: list[KpiValue]
    business_effect: list[KpiValue]
    is_profitable: bool
    executive_conclusion: str
    requests_by_day: list[dict[str, Any]]
    cost_and_savings_by_month: list[dict[str, Any]]
    top_agents: list[dict[str, Any]]
    top_scenarios: list[dict[str, Any]]
    issues_and_recommendations: list[dict[str, Any]]
    best_practices: list[dict[str, Any]]
    applied_filters: dict[str, str]


class AnalyticsListResponse(BaseModel):
    period: PeriodResponse
    provenance: DataProvenance
    items: list[dict[str, Any]]
    summary: dict[str, Any] = {}
    applied_filters: dict[str, str] = {}


class MethodologyResponse(BaseModel):
    average_monthly_fte_cost: float = Field(ge=0)
    monthly_work_hours_per_fte: float = Field(gt=0)
    monthly_work_minutes_per_fte: float = Field(gt=0)
    include_development_team: bool
    electricity_price_per_kwh: float = Field(ge=0)
    hardware_depreciation_months: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    calculation_period: Literal["month", "quarter", "year"]
    profitability_thresholds: dict[str, float]
    best_practice_rules: dict[str, float]
    model_tariffs: list[dict[str, Any]] = []
    scenario_benchmarks: list[dict[str, Any]] = []
    data_status: DataStatus = "demo"


class MethodologyUpdate(BaseModel):
    average_monthly_fte_cost: float = Field(ge=0)
    monthly_work_hours_per_fte: float = Field(gt=0)
    include_development_team: bool
    electricity_price_per_kwh: float = Field(ge=0)
    hardware_depreciation_months: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    calculation_period: Literal["month", "quarter", "year"]
    profitability_thresholds: dict[str, float]
    best_practice_rules: dict[str, float]

    @model_validator(mode="after")
    def validate_thresholds(self) -> MethodologyUpdate:
        profitable = self.profitability_thresholds.get("profitable_roi_percent")
        needs_review = self.profitability_thresholds.get("needs_review_roi_percent")
        if profitable is None or needs_review is None or profitable < needs_review:
            raise ValueError("profitability thresholds are incomplete or inconsistent")
        return self


CostCategory = Literal[
    "token",
    "inference",
    "subscription",
    "hardware_depreciation",
    "electricity",
    "infrastructure",
    "support",
    "development_team",
    "other",
]
AllocationType = Literal["requests", "tokens", "inference_time", "fixed_share", "agent"]


class CostComponentInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: CostCategory
    amount: float = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    period: str = Field(default="month", max_length=30)
    allocation_type: AllocationType
    agent_id: str | None = None
    model_id: str | None = None
    department_id: str | None = None
    effective_from: datetime
    effective_to: datetime | None = None
    source: str = Field(min_length=1, max_length=255)
    is_estimated: bool = False
    fixed_shares: dict[str, float] = {}

    @model_validator(mode="after")
    def validate_component(self) -> CostComponentInput:
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be later than effective_from")
        if self.allocation_type == "agent" and not self.agent_id:
            raise ValueError("agent_id is required for agent allocation")
        if self.allocation_type == "fixed_share":
            if not self.fixed_shares or any(value < 0 for value in self.fixed_shares.values()):
                raise ValueError("fixed_shares must contain non-negative values")
            if abs(sum(self.fixed_shares.values()) - 1) > 0.0001:
                raise ValueError("fixed_shares must sum to 1")
        return self


class CostComponentResponse(CostComponentInput):
    id: str


class PracticeActionRequest(BaseModel):
    actor: str = Field(default="demo-reviewer", min_length=1, max_length=255)
    comment: str | None = Field(default=None, max_length=1000)


class PracticeRecommendRequest(BaseModel):
    departments: list[str] = Field(min_length=1, max_length=50)
    owner: str | None = Field(default=None, max_length=255)
    comment: str | None = Field(default=None, max_length=1000)


class PracticeAdoptionInput(BaseModel):
    target_department: str = Field(min_length=1, max_length=255)
    status: Literal["recommended", "accepted", "pilot", "adopted", "rejected", "paused"]
    active_users: int = Field(default=0, ge=0)
    usages: int = Field(default=0, ge=0)
    time_saved_after_adoption: float = Field(default=0, ge=0)
    money_saved_after_adoption: float = Field(default=0, ge=0)
    owner: str | None = Field(default=None, max_length=255)
    comment: str | None = Field(default=None, max_length=1000)
