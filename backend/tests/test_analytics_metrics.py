from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient

from app.api.deps import get_analytics_repository
from app.main import app
from app.repositories.analytics_repository import AnalyticsFilters
from app.schemas.analytics import OverviewResponse


class FakeAnalyticsRepository:
    def __init__(self) -> None:
        self.filters: AnalyticsFilters | None = None

    async def overview(self, filters: AnalyticsFilters) -> dict[str, Any]:
        self.filters = filters
        return {
            "total_requests": 2,
            "successful_requests": 1,
            "failed_requests": 1,
            "success_rate": 50,
            "error_rate": 50,
            "avg_latency_ms": 120,
            "median_latency_ms": 110,
            "p95_latency_ms": 190,
            "avg_time_to_first_token_ms": 30,
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "avg_tokens_per_request": 75,
            "total_cost": Decimal("0.12345678901234"),
            "avg_cost_per_request": Decimal("0.06172839450617"),
            "unique_users": 1,
            "requests_by_model": [{"model": "m", "requests": 2}],
            "errors_by_type": [{"error_type": "timeout", "count": 1}],
            "requests_by_day": [
                {"date": datetime(2026, 7, 25, tzinfo=UTC), "requests": 2}
            ],
        }

    async def models(self, filters: AnalyticsFilters) -> list[dict[str, Any]]:
        self.filters = filters
        return [
            {
                "model": "m",
                "requests": 2,
                "success_rate": 50,
                "error_rate": 50,
                "avg_latency_ms": 120,
                "p95_latency_ms": 190,
                "total_tokens": 150,
                "total_cost": Decimal("0.12"),
                "avg_cost_per_request": Decimal("0.06"),
            }
        ]

    async def errors(self, filters: AnalyticsFilters) -> list[dict[str, Any]]:
        self.filters = filters
        return [
            {
                "error_type": "timeout",
                "count": 1,
                "share": 100,
                "affected_models": ["m"],
                "affected_scenarios": ["assistant"],
            }
        ]

    async def usage(self, filters: AnalyticsFilters, _: datetime) -> dict[str, Any]:
        self.filters = filters
        return {
            "dau": 1,
            "wau": 2,
            "mau": 3,
            "requests_per_user": 2.5,
            "requests_by_department": [{"department": "IT", "requests": 4}],
            "requests_by_scenario": [{"scenario": "assistant", "requests": 4}],
        }


def test_money_is_rounded_only_at_json_serialization() -> None:
    payload = FakeAnalyticsRepository()
    response = OverviewResponse.model_validate(
        __import__("asyncio").run(payload.overview(AnalyticsFilters()))
    )
    assert response.total_cost == Decimal("0.12345678901234")
    assert response.model_dump(mode="json")["total_cost"] == 0.123456789012


def test_all_analytics_endpoints_and_filters() -> None:
    repository = FakeAnalyticsRepository()
    app.dependency_overrides[get_analytics_repository] = lambda: repository
    client = TestClient(app)
    try:
        overview = client.get(
            "/api/analytics/overview",
            params={
                "date_from": "2026-07-01T00:00:00Z",
                "date_to": "2026-08-01T00:00:00Z",
                "model": "m",
                "department": "IT",
                "scenario": "assistant",
            },
        )
        models = client.get("/api/analytics/models")
        errors = client.get("/api/analytics/errors")
        usage = client.get("/api/analytics/usage")
    finally:
        app.dependency_overrides.pop(get_analytics_repository, None)

    assert overview.status_code == 200
    assert overview.json()["total_requests"] == 2
    assert overview.json()["total_cost"] == 0.123456789012
    assert models.status_code == 200 and models.json()[0]["p95_latency_ms"] == 190
    assert errors.status_code == 200 and errors.json()[0]["affected_models"] == ["m"]
    assert usage.status_code == 200 and usage.json()["mau"] == 3


def test_invalid_period_is_rejected() -> None:
    repository = FakeAnalyticsRepository()
    app.dependency_overrides[get_analytics_repository] = lambda: repository
    client = TestClient(app)
    try:
        response = client.get(
            "/api/analytics/overview",
            params={
                "date_from": "2026-08-01T00:00:00Z",
                "date_to": "2026-07-01T00:00:00Z",
            },
        )
    finally:
        app.dependency_overrides.pop(get_analytics_repository, None)
    assert response.status_code == 422
