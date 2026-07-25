import uuid
from types import SimpleNamespace

import pytest

from app.domain.best_practices import (
    PracticeSignals,
    RuleBasedBestPracticeClassifier,
    build_recommendation,
)
from app.domain.dataset_validation import parse_and_validate
from app.main import app
from app.services.best_practice_detection import BestPracticeDetectionService


def _signals(**overrides) -> PracticeSignals:
    values = {
        "scenario_id": uuid.uuid4(),
        "title": "Проверка договоров",
        "description": "Единый сценарий проверки",
        "departments": ("Юридический отдел",),
        "models": ("GigaChat Pro",),
        "user_count": 20,
        "usage_count": 50,
        "scenario_share": 0.4,
        "average_rating": 5.0,
        "rating_count": 20,
        "time_saved_hours": 40.0,
        "time_saved_count": 20,
        "success_rate": 0.95,
        "error_rate": 0.05,
        "success_count": 20,
        "growth_rate": 0.4,
        "timestamp_count": 50,
        "scenario_cohesion": 0.9,
    }
    values.update(overrides)
    return PracticeSignals(**values)


def test_impact_score_is_bounded_and_candidate_is_detected() -> None:
    decision = RuleBasedBestPracticeClassifier().evaluate(_signals())

    assert decision.is_candidate is True
    assert decision.impact_score >= 95
    assert 0 <= decision.confidence_score <= 100


def test_sparse_dataset_can_detect_repeatable_practice_with_lower_confidence() -> None:
    decision = RuleBasedBestPracticeClassifier().evaluate(
        _signals(
            user_count=0,
            usage_count=5,
            scenario_share=0.2,
            average_rating=None,
            rating_count=0,
            time_saved_hours=0,
            time_saved_count=0,
            success_rate=0.0,
            error_rate=0.0,
            success_count=0,
            growth_rate=0.0,
            timestamp_count=0,
            scenario_cohesion=0.8,
        )
    )

    assert decision.is_candidate is True
    assert decision.confidence_score < 70
    assert set(decision.missing_signals) == {"users", "rating", "time_saved", "success", "trend"}


def test_explicitly_poor_outcomes_reject_candidate() -> None:
    decision = RuleBasedBestPracticeClassifier().evaluate(
        _signals(average_rating=2.0, success_rate=0.3, error_rate=0.7)
    )

    assert decision.is_candidate is False
    assert "positive_rating" not in decision.reasons


@pytest.mark.asyncio
async def test_detector_persists_practice_for_plain_repeated_prompts() -> None:
    stored = []

    class RepositoryStub:
        async def existing_scenario_ids(self, **_kwargs):
            return set()

        async def create(self, practice):
            stored.append(practice)
            return practice

    scenario_id = uuid.uuid4()
    record_ids = [uuid.uuid4() for _ in range(3)]
    scenario = SimpleNamespace(
        id=scenario_id,
        is_noise=False,
        name="Сводка встречи",
        description="Повторяющиеся запросы на подготовку краткой сводки.",
        cluster_label=1,
        category_ids=["summarization"],
        share=0.3,
        quality={"cohesion": 0.82},
    )
    records = [
        SimpleNamespace(id=record_id, metadata_json={}, timestamp=None)
        for record_id in record_ids
    ]
    members = {
        scenario_id: [SimpleNamespace(record_id=record_id) for record_id in record_ids]
    }
    run = SimpleNamespace(
        tenant_id=uuid.uuid4(),
        model_provenance={"model": "gemini-2.5-flash"},
    )

    created = await BestPracticeDetectionService(RepositoryStub()).detect_for_run(
        run=run,
        scenarios=[scenario],
        members_by_scenario=members,
        records=records,
    )

    assert created == stored
    assert len(created) == 1
    assert created[0].title == "Сводка встречи"
    assert created[0].detection_evidence["classifier"] == "rule-based-v2"
    assert created[0].detection_evidence["outcome_evidence_available"] is False
    assert "rating" in created[0].detection_evidence["missing_signals"]


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
