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
    average_rating: float | None
    time_saved_hours: float
    success_rate: float
    error_rate: float
    growth_rate: float
    scenario_cohesion: float


@dataclass(frozen=True)
class DetectionDecision:
    is_candidate: bool
    impact_score: float
    confidence_score: float
    reasons: tuple[str, ...]


class BestPracticeClassifier(Protocol):
    """Boundary that can later be implemented by an AI classifier."""

    def evaluate(self, signals: PracticeSignals) -> DetectionDecision: ...


class RuleBasedBestPracticeClassifier:
    """Transparent MVP classifier based only on aggregate usage signals."""

    def __init__(
        self,
        *,
        min_impact_score: float = 70.0,
        min_usage_count: int = 8,
        min_user_count: int = 3,
        min_success_rate: float = 0.80,
        min_average_rating: float = 4.0,
        max_error_rate: float = 0.20,
        min_growth_rate: float = 0.05,
        min_time_saved_hours: float = 1.0,
    ) -> None:
        self.min_impact_score = min_impact_score
        self.min_usage_count = min_usage_count
        self.min_user_count = min_user_count
        self.min_success_rate = min_success_rate
        self.min_average_rating = min_average_rating
        self.max_error_rate = max_error_rate
        self.min_growth_rate = min_growth_rate
        self.min_time_saved_hours = min_time_saved_hours

    def calculate_impact_score(self, signals: PracticeSignals) -> float:
        user_score = _clamp(signals.user_count / 20)
        frequency_score = _clamp(signals.usage_count / 50)
        rating_score = (
            _clamp((signals.average_rating - 1) / 4)
            if signals.average_rating is not None
            else 0.5
        )
        time_score = _clamp(signals.time_saved_hours / 40)
        success_score = _clamp(signals.success_rate)

        weighted = (
            user_score * 0.20
            + frequency_score * 0.20
            + rating_score * 0.20
            + time_score * 0.20
            + success_score * 0.20
        )
        return round(weighted * 100, 1)

    def evaluate(self, signals: PracticeSignals) -> DetectionDecision:
        impact_score = self.calculate_impact_score(signals)
        checks = {
            "high_impact": impact_score >= self.min_impact_score,
            "frequent_usage": signals.usage_count >= self.min_usage_count,
            "multi_user_adoption": signals.user_count >= self.min_user_count,
            "high_success": signals.success_rate >= self.min_success_rate,
            "low_error_rate": signals.error_rate <= self.max_error_rate,
            "positive_rating": (
                signals.average_rating is not None
                and signals.average_rating >= self.min_average_rating
            ),
            "growing_usage": signals.growth_rate >= self.min_growth_rate,
            "confirmed_time_saving": signals.time_saved_hours >= self.min_time_saved_hours,
        }
        completeness = sum(
            (
                bool(signals.departments),
                bool(signals.models),
                signals.user_count > 0,
                signals.average_rating is not None,
                signals.time_saved_hours > 0,
                signals.usage_count > 0,
            )
        ) / 6
        confidence = round(
            100
            * _clamp(
                completeness * 0.55
                + _clamp(signals.scenario_cohesion) * 0.30
                + min(signals.usage_count / 30, 1) * 0.15
            ),
            1,
        )
        return DetectionDecision(
            is_candidate=all(checks.values()),
            impact_score=impact_score,
            confidence_score=confidence,
            reasons=tuple(name for name, passed in checks.items() if passed),
        )


def build_recommendation(signals: PracticeSignals) -> str:
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
