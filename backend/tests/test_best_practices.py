import uuid

import pytest

from app.domain.best_practices import (
    PracticeSignals,
    RuleBasedBestPracticeClassifier,
    build_recommendation,
)
from app.domain.dataset_validation import parse_and_validate
from app.main import app


def _signals(**overrides) -> PracticeSignals:
    values = {
        "scenario_id": uuid.uuid4(),
        "title": "Проверка договоров",
        "description": "Единый сценарий проверки",
        "departments": ("Юридический отдел",),
        "models": ("GigaChat Pro",),
        "user_count": 20,
        "usage_count": 50,
        "average_rating": 5.0,
        "time_saved_hours": 40.0,
        "success_rate": 0.95,
        "error_rate": 0.05,
        "growth_rate": 0.4,
        "scenario_cohesion": 0.9,
    }
    values.update(overrides)
    return PracticeSignals(**values)


def test_impact_score_is_bounded_and_candidate_is_detected() -> None:
    decision = RuleBasedBestPracticeClassifier().evaluate(_signals())

    assert decision.is_candidate is True
    assert decision.impact_score == pytest.approx(99.0)
    assert 0 <= decision.confidence_score <= 100


def test_missing_user_rating_and_success_prevents_detection() -> None:
    decision = RuleBasedBestPracticeClassifier().evaluate(
        _signals(user_count=0, average_rating=None, success_rate=0.0, error_rate=1.0)
    )

    assert decision.is_candidate is False
    assert "positive_rating" not in decision.reasons


def test_legal_recommendation_targets_procurement() -> None:
    recommendation = build_recommendation(_signals())

    assert "отдел закупок" in recommendation


def test_allowed_metrics_are_parsed_from_metadata_json() -> None:
    raw = (
        'text,user_id,team,metadata\n'
        'Проверь договор,u-1,Legal,"{""rating"":4.8,""time_saved_minutes"":35,'
        '""success"":true,""model"":""GigaChat Pro"",""secret"":""ignored""}"\n'
    ).encode()

    result = parse_and_validate(raw, max_row_chars=1000)

    assert result.accepted == 1
    assert result.rows[0].metadata["rating"] == 4.8
    assert result.rows[0].metadata["success"] is True
    assert result.rows[0].metadata["model"] == "GigaChat Pro"
    assert "secret" not in result.rows[0].metadata


def test_best_practice_routes_are_in_openapi() -> None:
    paths = app.openapi()["paths"]

    assert "/api/best-practices" in paths
    assert "/api/best-practices/top" in paths
    assert "/api/best-practices/{practice_id}/approve" in paths
    assert "/api/best-practices/{practice_id}/publish" in paths
