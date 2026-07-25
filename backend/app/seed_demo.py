"""Seed configurable enterprise entities for the documented demo story.

The high-volume request series remains a clearly labelled aggregate fixture in
``app.demo_enterprise``; this command seeds only durable configuration and
workflow entities. It is idempotent and never stores prompt content.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.demo_enterprise import (
    DEMO_ADOPTIONS,
    DEMO_BENCHMARKS,
    DEMO_COST_COMPONENTS,
    DEMO_METHODOLOGY,
    DEMO_MODEL_TARIFFS,
    DEMO_PRACTICES,
)
from app.domain.enums import BestPracticeStatus, PracticeAdoptionStatus
from app.infrastructure.db.models import (
    BestPractice,
    CostComponent,
    MethodologySettings,
    ModelTariff,
    PracticeAdoption,
    ScenarioBenchmark,
    Tenant,
)
from app.infrastructure.db.session import AsyncSessionLocal
from app.repositories.dataset_repository import DEMO_TENANT_ID

NAMESPACE = uuid.UUID("f0d22c8c-6011-45b7-9170-d070b1f4a908")


def _id(value: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, value)


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        tenant = await session.get(Tenant, DEMO_TENANT_ID)
        if tenant is None:
            session.add(Tenant(id=DEMO_TENANT_ID, name="CROC AI Lab (demo)"))
            # SQLAlchemy has no ORM relationship between all tenant-owned
            # entities, so make the FK parent visible before bulk inserts.
            await session.flush()

        methodology = (
            await session.execute(
                select(MethodologySettings).where(
                    MethodologySettings.tenant_id == DEMO_TENANT_ID
                )
            )
        ).scalar_one_or_none()
        if methodology is None:
            session.add(
                MethodologySettings(
                    tenant_id=DEMO_TENANT_ID,
                    average_monthly_fte_cost=Decimal(
                        str(DEMO_METHODOLOGY["average_monthly_fte_cost"])
                    ),
                    monthly_work_hours_per_fte=Decimal(
                        str(DEMO_METHODOLOGY["monthly_work_hours_per_fte"])
                    ),
                    include_development_team=bool(
                        DEMO_METHODOLOGY["include_development_team"]
                    ),
                    electricity_price_per_kwh=Decimal(
                        str(DEMO_METHODOLOGY["electricity_price_per_kwh"])
                    ),
                    hardware_depreciation_months=int(
                        DEMO_METHODOLOGY["hardware_depreciation_months"]
                    ),
                    currency="RUB",
                    calculation_period="month",
                    profitability_thresholds=DEMO_METHODOLOGY[
                        "profitability_thresholds"
                    ],
                    best_practice_rules=DEMO_METHODOLOGY["best_practice_rules"],
                )
            )

        for tariff in DEMO_MODEL_TARIFFS:
            tariff_id = _id(f"tariff:{tariff['model_name']}:{tariff['effective_from']}")
            if await session.get(ModelTariff, tariff_id) is None:
                session.add(
                    ModelTariff(
                        id=tariff_id,
                        model_name=str(tariff["model_name"]),
                        input_price_per_1m_tokens=Decimal(
                            str(tariff["input_price_per_1m_tokens"])
                        ),
                        output_price_per_1m_tokens=Decimal(
                            str(tariff["output_price_per_1m_tokens"])
                        ),
                        currency="RUB",
                        effective_from=_datetime(str(tariff["effective_from"])),
                        effective_to=_datetime(tariff["effective_to"]),
                    )
                )

        for component in DEMO_COST_COMPONENTS:
            component_id = _id(str(component["id"]))
            if await session.get(CostComponent, component_id) is None:
                session.add(
                    CostComponent(
                        id=component_id,
                        name=str(component["name"]),
                        category=str(component["category"]),
                        amount=Decimal(str(component["amount"])),
                        currency="RUB",
                        period=str(component["period"]),
                        allocation_type=str(component["allocation_type"]),
                        agent_id=component["agent_id"],
                        model_id=component["model_id"],
                        department_id=component["department_id"],
                        effective_from=_datetime(str(component["effective_from"])),
                        effective_to=_datetime(component["effective_to"]),
                        source=str(component["source"]),
                        is_estimated=bool(component["is_estimated"]),
                        fixed_shares=component["fixed_shares"],
                    )
                )

        for benchmark in DEMO_BENCHMARKS:
            benchmark_id = _id(f"benchmark:{benchmark['scenario_id']}")
            if await session.get(ScenarioBenchmark, benchmark_id) is None:
                session.add(
                    ScenarioBenchmark(
                        id=benchmark_id,
                        scenario_id=str(benchmark["scenario_id"]),
                        scenario_name=str(benchmark["scenario_name"]),
                        department=str(benchmark["department"]),
                        baseline_minutes_without_ai=Decimal(
                            str(benchmark["baseline_minutes_without_ai"])
                        ),
                        actual_minutes_with_ai=Decimal(
                            str(benchmark["actual_minutes_with_ai"])
                        ),
                        minutes_saved_per_task=Decimal(
                            str(benchmark["minutes_saved_per_task"])
                        ),
                        source_type=str(benchmark["source_type"]),
                        sample_size=int(benchmark["sample_size"]),
                        confidence_level=Decimal(str(benchmark["confidence_level"])),
                        approved_by=benchmark["approved_by"],
                        approved_at=_datetime(benchmark["approved_at"]),
                        is_estimated=bool(benchmark["is_estimated"]),
                        effective_from=datetime(2026, 7, 1, tzinfo=UTC),
                        effective_to=None,
                    )
                )

        practice_ids: dict[str, uuid.UUID] = {}
        for practice in DEMO_PRACTICES:
            practice_id = _id(str(practice["id"]))
            practice_ids[str(practice["id"])] = practice_id
            if await session.get(BestPractice, practice_id) is None:
                session.add(
                    BestPractice(
                        id=practice_id,
                        tenant_id=DEMO_TENANT_ID,
                        source_scenario_id=None,
                        title=str(practice["title"]),
                        short_description=str(practice["short_description"]),
                        department=str(practice["department_origin"]),
                        department_origin=str(practice["department_origin"]),
                        scenario=str(practice["title"]),
                        detected_at=_datetime(str(practice["detected_at"])),
                        status=BestPracticeStatus(str(practice["status"])),
                        confidence_score=float(practice["confidence_score"]),
                        impact_score=float(practice["impact_score"]),
                        adoption_count=int(practice["adoption_count"]),
                        estimated_time_saved=float(practice["estimated_time_saved"]),
                        estimated_fte_saved=float(practice["estimated_fte_saved"]),
                        estimated_money_saved=Decimal(
                            str(practice["estimated_money_saved"])
                        ),
                        tags=practice["tags"],
                        recommendation="Требуется экспертная проверка перед масштабированием.",
                        user_count=int(practice["user_count"]),
                        usage_count=int(practice["usage_count"]),
                        success_rate=0.95,
                        error_rate=0.05,
                        growth_rate=0.24,
                        departments=[practice["department_origin"]],
                        models=[],
                        detection_evidence={
                            "classifier": "rule-based-v1",
                            "is_estimated": practice["is_estimated"],
                        },
                        approved_by=practice["approved_by"],
                        approved_at=_datetime(practice["approved_at"]),
                        recommended_departments=practice["recommended_departments"],
                    )
                )

        await session.flush()
        for external_practice_id, rows in DEMO_ADOPTIONS.items():
            for adoption in rows:
                adoption_id = _id(str(adoption["id"]))
                if await session.get(PracticeAdoption, adoption_id) is None:
                    session.add(
                        PracticeAdoption(
                            id=adoption_id,
                            practice_id=practice_ids[external_practice_id],
                            target_department=str(adoption["target_department"]),
                            status=PracticeAdoptionStatus(str(adoption["status"])),
                            recommended_at=_datetime(str(adoption["recommended_at"])),
                            accepted_at=_datetime(adoption["accepted_at"]),
                            first_usage_at=_datetime(adoption["first_usage_at"]),
                            active_users=int(adoption["active_users"]),
                            usages=int(adoption["usages"]),
                            time_saved_after_adoption=Decimal(
                                str(adoption["time_saved_after_adoption"])
                            ),
                            money_saved_after_adoption=Decimal(
                                str(adoption["money_saved_after_adoption"])
                            ),
                            owner=adoption["owner"],
                            comment=adoption["comment"],
                        )
                    )
        await session.commit()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
