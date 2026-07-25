"""Rule-based best-practice scoring with an replaceable classifier boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class PracticeSignals:
    scenario_id: UUID
    title: str
    description: str
    departments: tuple[str, ...]
    models: tuple[str, ...]
    user_count: int
    usage_count: int
    scenario_share: float
    average_rating: float | None
    rating_count: int
    time_saved_hours: float
    time_saved_count: int
    success_rate: float
    error_rate: float
    success_count: int
    growth_rate: float
    timestamp_count: int
    scenario_cohesion: float

    @property
    def has_outcome_evidence(self) -> bool:
        return self.rating_count > 0 or self.time_saved_count > 0 or self.success_count > 0


@dataclass(frozen=True)
class DetectionDecision:
    is_candidate: bool
    impact_score: float
    confidence_score: float
    reasons: tuple[str, ...]
    missing_signals: tuple[str, ...] = ()


class BestPracticeClassifier(Protocol):
    """Boundary that can later be implemented by an AI classifier."""

    def evaluate(self, signals: PracticeSignals) -> DetectionDecision: ...


class RuleBasedBestPracticeClassifier:
    """Transparent classifier based only on aggregate usage signals.

    Business outcome columns are optional in an uploaded dataset. Their
    absence lowers confidence but must not make repeated, cohesive scenarios
    impossible to discover. Explicitly poor outcome values still reject a
    candidate.
    """

    def __init__(
        self,
        *,
        min_impact_score: float = 45.0,
        min_usage_count: int = 3,
        min_scenario_share: float = 0.05,
        min_scenario_cohesion: float = 0.45,
        min_success_rate: float = 0.65,
        min_average_rating: float = 3.5,
        max_error_rate: float = 0.35,
    ) -> None:
        self.min_impact_score = min_impact_score
        self.min_usage_count = min_usage_count
        self.min_scenario_share = min_scenario_share
        self.min_scenario_cohesion = min_scenario_cohesion
        self.min_success_rate = min_success_rate
        self.min_average_rating = min_average_rating
        self.max_error_rate = max_error_rate

    def calculate_impact_score(self, signals: PracticeSignals) -> float:
        components: list[tuple[float, float]] = [
            (_clamp(signals.usage_count / 8), 0.25),
            (_clamp(signals.scenario_share / 0.25), 0.20),
            (_clamp(signals.scenario_cohesion), 0.20),
        ]
        if signals.user_count > 0:
            components.append((_clamp(signals.user_count / 5), 0.10))
        if signals.rating_count > 0 and signals.average_rating is not None:
            components.append((_clamp((signals.average_rating - 1) / 4), 0.10))
        if signals.time_saved_count > 0:
            components.append((_clamp(signals.time_saved_hours / 5), 0.10))
        if signals.success_count > 0:
            components.append((_clamp(signals.success_rate), 0.10))
        if signals.timestamp_count >= 4:
            components.append((_clamp((signals.growth_rate + 0.25) / 0.75), 0.05))

        total_weight = sum(weight for _, weight in components)
        weighted = sum(score * weight for score, weight in components) / total_weight
        return round(weighted * 100, 1)

    def evaluate(self, signals: PracticeSignals) -> DetectionDecision:
        impact_score = self.calculate_impact_score(signals)
        checks: dict[str, bool] = {
            "high_impact": impact_score >= self.min_impact_score,
            "repeated_usage": signals.usage_count >= self.min_usage_count,
            "meaningful_share": signals.scenario_share >= self.min_scenario_share,
            "cohesive_scenario": signals.scenario_cohesion >= self.min_scenario_cohesion,
        }
        if signals.rating_count > 0:
            checks["positive_rating"] = bool(
                signals.average_rating is not None
                and signals.average_rating >= self.min_average_rating
            )
        if signals.success_count > 0:
            checks["high_success"] = signals.success_rate >= self.min_success_rate
            checks["low_error_rate"] = signals.error_rate <= self.max_error_rate

        missing_signals = tuple(
            name
            for name, missing in (
                ("users", signals.user_count == 0),
                ("rating", signals.rating_count == 0),
                ("time_saved", signals.time_saved_count == 0),
                ("success", signals.success_count == 0),
                ("trend", signals.timestamp_count < 4),
            )
            if missing
        )
        optional_completeness = 1 - len(missing_signals) / 5
        confidence = round(
            100
            * _clamp(
                _clamp(signals.scenario_cohesion) * 0.40
                + min(signals.usage_count / 12, 1) * 0.25
                + optional_completeness * 0.35
            ),
            1,
        )
        return DetectionDecision(
            is_candidate=all(checks.values()),
            impact_score=impact_score,
            confidence_score=confidence,
            reasons=tuple(name for name, passed in checks.items() if passed),
            missing_signals=missing_signals,
        )


def build_recommendation(signals: PracticeSignals) -> str:
    if not signals.has_outcome_evidence:
        return (
            "Radar обнаружил устойчивый повторяемый сценарий. "
            "Проверьте качество результата и экономию времени на пилоте, "
            "после подтверждения масштабируйте практику."
        )
    if len(signals.departments) > 1:
        return "Практика уже распространяется между подразделениями. Рекомендуется масштабирование."

    department = signals.departments[0] if signals.departments else "одним подразделением"
    title = signals.title.lower()
    if "договор" in title or "юрид" in department.lower():
        return (
            f"Используется только подразделением «{department}». "
            "Рекомендуется внедрение в отдел закупок."
        )
    if "отч" in title or "данн" in title:
        return (
            f"Используется только подразделением «{department}». "
            "Рекомендуется внедрение в финансовом блоке."
        )
    return "Высокая эффективность. Рекомендуется масштабирование."
