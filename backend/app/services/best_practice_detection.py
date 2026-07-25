from __future__ import annotations

import uuid
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime

from app.domain.best_practices import (
    BestPracticeClassifier,
    PracticeSignals,
    RuleBasedBestPracticeClassifier,
    build_recommendation,
)
from app.domain.enums import BestPracticeStatus
from app.infrastructure.db.models import AnalysisRun, BestPractice, Record, Scenario, ScenarioMember
from app.repositories.best_practice_repository import BestPracticeRepository


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
    return None


def _boolean(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "success", "успех"}:
            return True
        if normalized in {"false", "0", "no", "failed", "ошибка"}:
            return False
    return None


def _growth_rate(records: list[Record]) -> float:
    timestamps = sorted(r.timestamp for r in records if r.timestamp is not None)
    if len(timestamps) < 4:
        return 0.0
    midpoint = timestamps[len(timestamps) // 2]
    previous = sum(1 for ts in timestamps if ts < midpoint)
    recent = len(timestamps) - previous
    return round((recent - previous) / max(previous, 1), 3)


class BestPracticeDetectionService:
    def __init__(
        self,
        repository: BestPracticeRepository,
        classifier: BestPracticeClassifier | None = None,
    ) -> None:
        self._repository = repository
        self._classifier = classifier or RuleBasedBestPracticeClassifier()

    async def detect_for_run(
        self,
        *,
        run: AnalysisRun,
        scenarios: Iterable[Scenario],
        members_by_scenario: dict[uuid.UUID, list[ScenarioMember]],
        records: Iterable[Record],
    ) -> list[BestPractice]:
        scenario_rows = [scenario for scenario in scenarios if not scenario.is_noise]
        existing_ids = await self._repository.existing_scenario_ids(
            tenant_id=run.tenant_id,
            scenario_ids=[scenario.id for scenario in scenario_rows],
        )
        record_by_id = {record.id: record for record in records}
        created: list[BestPractice] = []

        for scenario in scenario_rows:
            if scenario.id in existing_ids:
                continue
            scenario_records = [
                record_by_id[member.record_id]
                for member in members_by_scenario.get(scenario.id, [])
                if member.record_id in record_by_id
            ]
            signals = self._build_signals(run, scenario, scenario_records)
            decision = self._classifier.evaluate(signals)
            if not decision.is_candidate:
                continue

            primary_department = self._primary_department(scenario_records)
            practice = BestPractice(
                id=uuid.uuid4(),
                tenant_id=run.tenant_id,
                source_scenario_id=scenario.id,
                title=signals.title,
                short_description=signals.description,
                department=primary_department,
                scenario=signals.title,
                detected_at=datetime.now(UTC),
                status=BestPracticeStatus.DETECTED,
                confidence_score=decision.confidence_score,
                impact_score=decision.impact_score,
                adoption_count=signals.user_count,
                estimated_time_saved=round(signals.time_saved_hours, 2),
                estimated_fte_saved=round(signals.time_saved_hours / 160, 3),
                tags=sorted(set(scenario.category_ids + list(signals.models))),
                recommendation=build_recommendation(signals),
                user_count=signals.user_count,
                usage_count=signals.usage_count,
                average_rating=signals.average_rating,
                success_rate=round(signals.success_rate, 3),
                error_rate=round(signals.error_rate, 3),
                growth_rate=round(signals.growth_rate, 3),
                departments=list(signals.departments),
                models=list(signals.models),
                detection_evidence={
                    "classifier": "rule-based-v2",
                    "matched_rules": list(decision.reasons),
                    "missing_signals": list(decision.missing_signals),
                    "scenario_cohesion": signals.scenario_cohesion,
                    "scenario_share": signals.scenario_share,
                    "outcome_evidence_available": signals.has_outcome_evidence,
                },
            )
            await self._repository.create(practice)
            created.append(practice)
        return created

    @staticmethod
    def _primary_department(records: list[Record]) -> str:
        values = [
            str(record.metadata_json.get("department") or record.metadata_json.get("team"))
            for record in records
            if record.metadata_json.get("department") or record.metadata_json.get("team")
        ]
        return Counter(values).most_common(1)[0][0] if values else "Не определено"

    @staticmethod
    def _build_signals(
        run: AnalysisRun, scenario: Scenario, records: list[Record]
    ) -> PracticeSignals:
        departments = sorted(
            {
                str(
                    record.metadata_json.get("department")
                    or record.metadata_json.get("team")
                    or record.metadata_json.get("direction")
                )
                for record in records
                if (
                    record.metadata_json.get("department")
                    or record.metadata_json.get("team")
                    or record.metadata_json.get("direction")
                )
            }
        )
        fallback_model = run.model_provenance.get("model")
        models = sorted(
            {
                str(record.metadata_json.get("model") or record.metadata_json.get("agent_id"))
                for record in records
                if record.metadata_json.get("model") or record.metadata_json.get("agent_id")
            }
        )
        if not models and fallback_model:
            models = [str(fallback_model)]

        users = {
            str(record.metadata_json["user_id"])
            for record in records
            if record.metadata_json.get("user_id")
        }
        ratings = [
            rating
            for record in records
            if (rating := _number(record.metadata_json.get("rating"))) is not None
            and 1 <= rating <= 5
        ]
        time_saved_values = [
            max(value, 0)
            for record in records
            if (value := _number(record.metadata_json.get("time_saved_minutes"))) is not None
        ]
        success_values: list[bool] = []
        error_values: list[bool] = []
        for record in records:
            success = _boolean(record.metadata_json.get("success"))
            error = _boolean(record.metadata_json.get("error"))
            if success is not None:
                success_values.append(success)
            elif error is not None:
                success_values.append(not error)
            if error is not None:
                error_values.append(error)
            elif success is not None:
                error_values.append(not success)

        average_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
        success_rate = (
            sum(1 for success in success_values if success) / len(success_values)
            if success_values
            else 0.0
        )
        error_rate = (
            sum(1 for error in error_values if error) / len(error_values)
            if error_values
            else 0.0
        )
        return PracticeSignals(
            scenario_id=scenario.id,
            title=scenario.name or f"Сценарий {scenario.cluster_label}",
            description=scenario.description or "Устойчивый сценарий эффективного использования ИИ.",
            departments=tuple(departments),
            models=tuple(models),
            user_count=len(users),
            usage_count=len(records),
            scenario_share=float(scenario.share),
            average_rating=average_rating,
            rating_count=len(ratings),
            time_saved_hours=sum(time_saved_values) / 60,
            time_saved_count=len(time_saved_values),
            success_rate=success_rate,
            error_rate=error_rate,
            success_count=max(len(success_values), len(error_values)),
            growth_rate=_growth_rate(records),
            timestamp_count=sum(record.timestamp is not None for record in records),
            scenario_cohesion=float(scenario.quality.get("cohesion", 0.0)),
        )
