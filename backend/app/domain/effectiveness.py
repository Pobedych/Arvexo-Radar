"""Pure, configurable calculations for Radar business-effectiveness metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

MILLION = Decimal(1000000)
HUNDRED = Decimal(100)
SIXTY = Decimal(60)

AllocationType = Literal["requests", "tokens", "inference_time", "fixed_share", "agent"]
EffectivenessStatus = Literal[
    "profitable", "needs_review", "loss_making", "insufficient_data"
]


def _decimal(value: Decimal | float | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _require_nonnegative(name: str, value: Decimal | float) -> Decimal:
    converted = _decimal(value)
    if converted < 0:
        raise ValueError(f"{name} must be non-negative")
    return converted


@dataclass(frozen=True, slots=True)
class ModelTariffValue:
    model_name: str
    input_price_per_1m_tokens: Decimal
    output_price_per_1m_tokens: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class MethodologyValue:
    average_monthly_fte_cost: Decimal
    monthly_work_hours_per_fte: Decimal
    currency: str
    calculation_period: str
    include_development_team: bool
    profitable_roi_percent: Decimal
    needs_review_roi_percent: Decimal

    @property
    def monthly_work_minutes_per_fte(self) -> Decimal:
        if self.monthly_work_hours_per_fte <= 0:
            raise ValueError("monthly_work_hours_per_fte must be positive")
        return self.monthly_work_hours_per_fte * SIXTY


@dataclass(frozen=True, slots=True)
class BusinessEffect:
    completed_tasks: int
    minutes_saved_per_task: Decimal
    time_saved_minutes: Decimal
    time_saved_hours: Decimal
    fte_saved: Decimal
    money_saved: Decimal
    total_ai_cost: Decimal
    net_benefit: Decimal
    roi_percent: Decimal | None
    payback_ratio: Decimal | None
    is_profitable: bool
    effectiveness_status: EffectivenessStatus
    is_estimated: bool
    confidence_level: Decimal
    period_months: Decimal


def calculate_token_cost(
    prompt_tokens: int,
    completion_tokens: int,
    tariff: ModelTariffValue | None,
) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    """Return input/output/request cost without inventing a missing tariff."""

    if prompt_tokens < 0 or completion_tokens < 0:
        raise ValueError("token counts must be non-negative")
    if tariff is None:
        return None, None, None
    input_price = _require_nonnegative(
        "input_price_per_1m_tokens", tariff.input_price_per_1m_tokens
    )
    output_price = _require_nonnegative(
        "output_price_per_1m_tokens", tariff.output_price_per_1m_tokens
    )
    input_cost = Decimal(prompt_tokens) / MILLION * input_price
    output_cost = Decimal(completion_tokens) / MILLION * output_price
    return input_cost, output_cost, input_cost + output_cost


def calculate_business_effect(
    *,
    completed_tasks: int,
    minutes_saved_per_task: Decimal | float,
    total_ai_cost: Decimal | float,
    methodology: MethodologyValue,
    confidence_level: Decimal | float,
    is_estimated: bool,
    period_months: Decimal | float = Decimal(1),
) -> BusinessEffect:
    """Calculate B, FTE equivalent, net benefit, ROI and payback.

    ``fte_saved`` is an average capacity equivalent for the requested period,
    never a count of positions removed.
    """

    if completed_tasks < 0:
        raise ValueError("completed_tasks must be non-negative")
    minutes_per_task = _require_nonnegative(
        "minutes_saved_per_task", minutes_saved_per_task
    )
    ai_cost = _require_nonnegative("total_ai_cost", total_ai_cost)
    monthly_fte_cost = _require_nonnegative(
        "average_monthly_fte_cost", methodology.average_monthly_fte_cost
    )
    months = _decimal(period_months)
    if months <= 0:
        raise ValueError("period_months must be positive")
    confidence = _decimal(confidence_level)
    if not Decimal(0) <= confidence <= Decimal(1):
        raise ValueError("confidence_level must be between 0 and 1")

    time_saved_minutes = Decimal(completed_tasks) * minutes_per_task
    time_saved_hours = time_saved_minutes / SIXTY
    fte_saved = time_saved_minutes / (methodology.monthly_work_minutes_per_fte * months)
    money_saved = fte_saved * monthly_fte_cost * months
    net_benefit = money_saved - ai_cost
    roi = net_benefit / ai_cost * HUNDRED if ai_cost > 0 else None
    payback = money_saved / ai_cost if ai_cost > 0 else None

    if completed_tasks == 0 or confidence < Decimal("0.5"):
        status: EffectivenessStatus = "insufficient_data"
    elif roi is None:
        status = "needs_review"
    elif roi >= methodology.profitable_roi_percent:
        status = "profitable"
    elif roi >= methodology.needs_review_roi_percent:
        status = "needs_review"
    else:
        status = "loss_making"

    return BusinessEffect(
        completed_tasks=completed_tasks,
        minutes_saved_per_task=minutes_per_task,
        time_saved_minutes=time_saved_minutes,
        time_saved_hours=time_saved_hours,
        fte_saved=fte_saved,
        money_saved=money_saved,
        total_ai_cost=ai_cost,
        net_benefit=net_benefit,
        roi_percent=roi,
        payback_ratio=payback,
        is_profitable=money_saved > ai_cost,
        effectiveness_status=status,
        is_estimated=is_estimated,
        confidence_level=confidence,
        period_months=months,
    )


@dataclass(frozen=True, slots=True)
class AllocationTarget:
    key: str
    requests: Decimal = Decimal(0)
    tokens: Decimal = Decimal(0)
    inference_time_ms: Decimal = Decimal(0)
    fixed_share: Decimal = Decimal(0)


def allocate_cost(
    amount: Decimal | float,
    allocation_type: AllocationType,
    targets: Sequence[AllocationTarget],
    *,
    direct_agent_id: str | None = None,
) -> dict[str, Decimal]:
    """Allocate a shared cost deterministically and preserve the total exactly."""

    total_amount = _require_nonnegative("amount", amount)
    if not targets:
        return {}
    keys = [target.key for target in targets]
    if len(keys) != len(set(keys)):
        raise ValueError("allocation target keys must be unique")

    if allocation_type == "agent":
        if direct_agent_id is None or direct_agent_id not in keys:
            raise ValueError("direct_agent_id must identify an allocation target")
        return {key: total_amount if key == direct_agent_id else Decimal(0) for key in keys}

    attribute = {
        "requests": "requests",
        "tokens": "tokens",
        "inference_time": "inference_time_ms",
        "fixed_share": "fixed_share",
    }.get(allocation_type)
    if attribute is None:
        raise ValueError(f"unsupported allocation type: {allocation_type}")

    weights = [_require_nonnegative(attribute, getattr(target, attribute)) for target in targets]
    weight_sum = sum(weights, Decimal(0))
    if weight_sum <= 0:
        raise ValueError(f"cannot allocate by {allocation_type}: total weight is zero")

    result: dict[str, Decimal] = {}
    allocated = Decimal(0)
    for index, (target, weight) in enumerate(zip(targets, weights, strict=True)):
        share = total_amount - allocated if index == len(targets) - 1 else total_amount * weight / weight_sum
        result[target.key] = share
        allocated += share
    return result


def total_ai_cost(
    components: Sequence[Mapping[str, object]], *, include_development_team: bool
) -> Decimal:
    total = Decimal(0)
    for component in components:
        category = str(component["category"])
        if category == "development_team" and not include_development_team:
            continue
        total += _require_nonnegative("component amount", component["amount"])  # type: ignore[arg-type]
    return total
