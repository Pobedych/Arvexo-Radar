from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


def _display_money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.000000000001")))


class ModelRequestCount(BaseModel):
    model: str
    requests: int


class ErrorTypeCount(BaseModel):
    error_type: str
    count: int


class DailyRequestCount(BaseModel):
    date: datetime
    requests: int


class OverviewResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    error_rate: float
    avg_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    avg_time_to_first_token_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    avg_tokens_per_request: float
    total_cost: Decimal
    avg_cost_per_request: Decimal
    unique_users: int
    requests_by_model: list[ModelRequestCount]
    errors_by_type: list[ErrorTypeCount]
    requests_by_day: list[DailyRequestCount]

    @field_serializer("total_cost", "avg_cost_per_request", when_used="json")
    def serialize_money(self, value: Decimal) -> float:
        return _display_money(value)


class ModelAnalytics(BaseModel):
    model: str
    requests: int
    success_rate: float
    error_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    total_cost: Decimal
    avg_cost_per_request: Decimal

    @field_serializer("total_cost", "avg_cost_per_request", when_used="json")
    def serialize_money(self, value: Decimal) -> float:
        return _display_money(value)


class ErrorAnalytics(BaseModel):
    error_type: str
    count: int
    share: float
    affected_models: list[str]
    affected_scenarios: list[str]


class DepartmentRequestCount(BaseModel):
    department: str
    requests: int


class ScenarioRequestCount(BaseModel):
    scenario: str
    requests: int


class UsageResponse(BaseModel):
    dau: int
    wau: int
    mau: int
    requests_per_user: float
    requests_by_department: list[DepartmentRequestCount]
    requests_by_scenario: list[ScenarioRequestCount]
