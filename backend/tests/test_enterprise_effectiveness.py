from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_enterprise_analytics_service
from app.domain.effectiveness import (
    AllocationTarget,
    MethodologyValue,
    ModelTariffValue,
    allocate_cost,
    calculate_business_effect,
    calculate_token_cost,
    total_ai_cost,
)
from app.main import app
from app.schemas.enterprise import PracticeAdoptionInput
from app.services.enterprise_analytics import EnterpriseAnalyticsService, EnterpriseFilters


@pytest.fixture
def methodology() -> MethodologyValue:
    return MethodologyValue(
        average_monthly_fte_cost=Decimal(400000),
        monthly_work_hours_per_fte=Decimal(160),
        currency="RUB",
        calculation_period="month",
        include_development_team=False,
        profitable_roi_percent=Decimal(20),
        needs_review_roi_percent=Decimal(0),
    )


def test_token_cost_uses_configured_ruble_tariff() -> None:
    tariff = ModelTariffValue(
        model_name="model-a",
        input_price_per_1m_tokens=Decimal("950.25"),
        output_price_per_1m_tokens=Decimal("1900.50"),
        currency="RUB",
    )
    input_cost, output_cost, request_cost = calculate_token_cost(250_000, 100_000, tariff)
    assert input_cost == Decimal("237.5625")
    assert output_cost == Decimal("190.050")
    assert request_cost == Decimal("427.6125")


def test_missing_tariff_does_not_invent_cost_and_negative_tokens_fail() -> None:
    assert calculate_token_cost(100, 20, None) == (None, None, None)
    with pytest.raises(ValueError, match="non-negative"):
        calculate_token_cost(-1, 0, None)


def test_tariff_change_mid_period_is_applied_per_request() -> None:
    old = ModelTariffValue("model-a", Decimal(1000), Decimal(2000), "RUB")
    new = ModelTariffValue("model-a", Decimal(1200), Decimal(2400), "RUB")
    first = calculate_token_cost(1_000_000, 500_000, old)[2]
    second = calculate_token_cost(1_000_000, 500_000, new)[2]
    assert first == Decimal(2000)
    assert second == Decimal(2400)
    assert first + second == Decimal(4400)  # type: ignore[operator]


@pytest.mark.parametrize(
    ("allocation_type", "expected"),
    [
        ("requests", {"a": Decimal(25), "b": Decimal(75)}),
        ("tokens", {"a": Decimal(20), "b": Decimal(80)}),
        ("inference_time", {"a": Decimal(40), "b": Decimal(60)}),
        ("fixed_share", {"a": Decimal(30), "b": Decimal(70)}),
    ],
)
def test_shared_cost_allocation_preserves_total(allocation_type: str, expected: dict) -> None:
    targets = [
        AllocationTarget("a", requests=Decimal(1), tokens=Decimal(1), inference_time_ms=Decimal(2), fixed_share=Decimal("0.3")),
        AllocationTarget("b", requests=Decimal(3), tokens=Decimal(4), inference_time_ms=Decimal(3), fixed_share=Decimal("0.7")),
    ]
    assert allocate_cost(Decimal(100), allocation_type, targets) == expected  # type: ignore[arg-type]


def test_direct_agent_allocation_and_zero_weight_validation() -> None:
    targets = [AllocationTarget("a"), AllocationTarget("b")]
    assert allocate_cost(90, "agent", targets, direct_agent_id="b") == {
        "a": Decimal(0),
        "b": Decimal(90),
    }
    with pytest.raises(ValueError, match="total weight is zero"):
        allocate_cost(90, "tokens", targets)


def test_time_fte_money_net_roi_and_b_greater_than_a(
    methodology: MethodologyValue,
) -> None:
    result = calculate_business_effect(
        completed_tasks=100,
        minutes_saved_per_task=30,
        total_ai_cost=100_000,
        methodology=methodology,
        confidence_level=Decimal("0.9"),
        is_estimated=False,
    )
    assert result.time_saved_minutes == Decimal(3000)
    assert result.time_saved_hours == Decimal(50)
    assert result.fte_saved == Decimal("0.3125")
    assert result.money_saved == Decimal(125000)
    assert result.net_benefit == Decimal(25000)
    assert result.roi_percent == Decimal(25)
    assert result.payback_ratio == Decimal("1.25")
    assert result.is_profitable is True
    assert result.effectiveness_status == "profitable"


def test_zero_cost_and_incomplete_estimate_are_explicit(
    methodology: MethodologyValue,
) -> None:
    result = calculate_business_effect(
        completed_tasks=10,
        minutes_saved_per_task=5,
        total_ai_cost=0,
        methodology=methodology,
        confidence_level=Decimal("0.3"),
        is_estimated=True,
    )
    assert result.roi_percent is None
    assert result.payback_ratio is None
    assert result.effectiveness_status == "insufficient_data"
    assert result.is_estimated is True


def test_different_periods_keep_money_consistent_and_normalize_fte(
    methodology: MethodologyValue,
) -> None:
    month = calculate_business_effect(
        completed_tasks=100,
        minutes_saved_per_task=30,
        total_ai_cost=1,
        methodology=methodology,
        confidence_level=1,
        is_estimated=False,
        period_months=1,
    )
    quarter = calculate_business_effect(
        completed_tasks=300,
        minutes_saved_per_task=30,
        total_ai_cost=3,
        methodology=methodology,
        confidence_level=1,
        is_estimated=False,
        period_months=3,
    )
    assert quarter.fte_saved == month.fte_saved
    assert quarter.money_saved == month.money_saved * 3


def test_total_ai_cost_respects_optional_development_team() -> None:
    components = [
        {"category": "token", "amount": Decimal(10)},
        {"category": "development_team", "amount": Decimal(30)},
    ]
    assert total_ai_cost(components, include_development_team=False) == Decimal(10)
    assert total_ai_cost(components, include_development_team=True) == Decimal(40)


def test_agent_and_department_aggregations_are_formula_consistent() -> None:
    service = EnterpriseAnalyticsService()
    agent_payload = service.agents(EnterpriseFilters())
    department_payload = service.departments(EnterpriseFilters())
    overview = service.overview(EnterpriseFilters())
    assert {item["status"] for item in agent_payload["items"]} >= {
        "profitable",
        "loss_making",
        "insufficient_data",
    }
    assert sum(item["requests"] for item in department_payload["items"]) == 28_400
    assert sum(item["cost"] for item in department_payload["items"]) == 1_170_000
    assert overview["is_profitable"] is True


def test_practice_status_transitions_and_adoption_flow() -> None:
    service = EnterpriseAnalyticsService()
    practice_id = "demo-policy-search"
    assert service.transition_practice(practice_id, "review", "expert")["status"] == "under_review"  # type: ignore[index]
    assert service.transition_practice(practice_id, "approve", "expert")["status"] == "approved"  # type: ignore[index]
    assert service.transition_practice(practice_id, "publish", "expert")["status"] == "published"  # type: ignore[index]
    scaled = service.recommend_practice(
        practice_id, ["Сервисный центр"], "owner", "Пилот"
    )
    assert scaled is not None and scaled["status"] == "scaling"
    adoption = service.upsert_adoption(
        practice_id,
        PracticeAdoptionInput(
            target_department="Сервисный центр",
            status="adopted",
            active_users=12,
            usages=44,
            time_saved_after_adoption=18,
            money_saved_after_adoption=45000,
        ),
    )
    assert adoption is not None and adoption["status"] == "adopted"
    assert adoption["first_usage_at"] is not None


def test_enterprise_api_contract_and_all_filters() -> None:
    service = EnterpriseAnalyticsService()
    app.dependency_overrides[get_enterprise_analytics_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.get(
            "/api/analytics/agents",
            params={
                "date_from": "2026-07-01T00:00:00Z",
                "date_to": "2026-08-01T00:00:00Z",
                "department": "Юридический отдел",
                "role": "Юрист",
                "agent": "legal-agent",
                "model": "GigaChat Pro",
                "scenario": "contract-review",
                "tool": "Корпоративные документы",
            },
        )
        methodology_response = client.get("/api/methodology")
        practice_response = client.post(
            "/api/best-practices/demo-policy-search/review",
            json={"actor": "expert"},
        )
    finally:
        app.dependency_overrides.pop(get_enterprise_analytics_service, None)
    assert response.status_code == 200 and len(response.json()["items"]) == 1
    assert response.json()["applied_filters"]["tool"] == "Корпоративные документы"
    assert methodology_response.status_code == 200
    assert methodology_response.json()["currency"] == "RUB"
    assert practice_response.status_code == 200


def test_required_enterprise_routes_are_in_openapi() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/api/analytics/agents",
        "/api/analytics/tools",
        "/api/analytics/departments",
        "/api/analytics/costs",
        "/api/analytics/business-effect",
        "/api/analytics/roi",
        "/api/methodology",
        "/api/cost-components",
        "/api/best-practices/{practice_id}/review",
        "/api/best-practices/{practice_id}/reject",
        "/api/best-practices/{practice_id}/recommend",
        "/api/best-practices/{practice_id}/adoption",
    }
    assert required <= paths.keys()
