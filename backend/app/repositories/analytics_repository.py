from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import LLMRequestEvent, ModelTariff


@dataclass(frozen=True, slots=True)
class AnalyticsFilters:
    date_from: datetime | None = None
    date_to: datetime | None = None
    model: str | None = None
    department: str | None = None
    scenario: str | None = None
    role: str | None = None
    user: str | None = None
    agent: str | None = None
    tool: str | None = None


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _conditions(
        filters: AnalyticsFilters, *, include_dates: bool = True
    ) -> list[Any]:
        conditions: list[Any] = []
        if include_dates and filters.date_from is not None:
            conditions.append(LLMRequestEvent.started_at >= filters.date_from)
        if include_dates and filters.date_to is not None:
            conditions.append(LLMRequestEvent.started_at < filters.date_to)
        if filters.model is not None:
            conditions.append(LLMRequestEvent.model == filters.model)
        if filters.department is not None:
            conditions.append(LLMRequestEvent.department == filters.department)
        if filters.scenario is not None:
            conditions.append(
                (LLMRequestEvent.scenario == filters.scenario)
                | (LLMRequestEvent.scenario_id == filters.scenario)
            )
        if filters.role is not None:
            conditions.append(LLMRequestEvent.role == filters.role)
        if filters.user is not None:
            conditions.append(LLMRequestEvent.user_id_hash == filters.user)
        if filters.agent is not None:
            conditions.append(LLMRequestEvent.agent_id == filters.agent)
        if filters.tool is not None:
            conditions.append(LLMRequestEvent.tool_calls.contains([{"name": filters.tool}]))
        return conditions

    async def find_tariff(
        self, model: str, at: datetime, currency: str
    ) -> ModelTariff | None:
        statement = (
            select(ModelTariff)
            .where(
                ModelTariff.model_name == model,
                ModelTariff.currency == currency,
                ModelTariff.effective_from <= at,
                (ModelTariff.effective_to.is_(None) | (ModelTariff.effective_to > at)),
            )
            .order_by(ModelTariff.effective_from.desc())
            .limit(1)
        )
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def add_event(self, event: LLMRequestEvent) -> None:
        if await self._session.get(LLMRequestEvent, event.request_id) is None:
            self._session.add(event)
            await self._session.flush()

    async def overview(self, filters: AnalyticsFilters) -> dict[str, Any]:
        conditions = self._conditions(filters)
        statement = select(
            func.count().label("total_requests"),
            func.count().filter(LLMRequestEvent.status == "success").label("successful_requests"),
            func.count().filter(LLMRequestEvent.status == "error").label("failed_requests"),
            func.avg(LLMRequestEvent.latency_ms).label("avg_latency_ms"),
            func.percentile_cont(0.5)
            .within_group(LLMRequestEvent.latency_ms)
            .label("median_latency_ms"),
            func.percentile_cont(0.95)
            .within_group(LLMRequestEvent.latency_ms)
            .label("p95_latency_ms"),
            func.avg(LLMRequestEvent.time_to_first_token_ms).label("avg_ttft_ms"),
            func.coalesce(func.sum(LLMRequestEvent.prompt_tokens), 0).label("prompt_tokens"),
            func.coalesce(func.sum(LLMRequestEvent.completion_tokens), 0).label(
                "completion_tokens"
            ),
            func.coalesce(func.sum(LLMRequestEvent.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(LLMRequestEvent.total_cost), Decimal(0)).label("total_cost"),
            func.count(distinct(LLMRequestEvent.user_id_hash)).label("unique_users"),
        ).where(*conditions)
        row = (await self._session.execute(statement)).mappings().one()
        total = int(row["total_requests"] or 0)
        successful = int(row["successful_requests"] or 0)
        failed = int(row["failed_requests"] or 0)
        total_tokens = int(row["total_tokens"] or 0)
        total_cost = Decimal(row["total_cost"] or 0)

        by_model_statement = (
            select(LLMRequestEvent.model, func.count().label("requests"))
            .where(*conditions)
            .group_by(LLMRequestEvent.model)
            .order_by(func.count().desc(), LLMRequestEvent.model)
        )
        normalized_error_type = func.coalesce(
            LLMRequestEvent.error_type, "internal_proxy_error"
        )
        by_error_statement = (
            select(normalized_error_type.label("error_type"), func.count().label("count"))
            .where(*conditions, LLMRequestEvent.status == "error")
            .group_by(normalized_error_type)
            .order_by(func.count().desc())
        )
        day = func.date_trunc("day", LLMRequestEvent.started_at)
        by_day_statement = (
            select(day.label("date"), func.count().label("requests"))
            .where(*conditions)
            .group_by(day)
            .order_by(day)
        )
        by_model = (await self._session.execute(by_model_statement)).mappings().all()
        by_error = (await self._session.execute(by_error_statement)).mappings().all()
        by_day = (await self._session.execute(by_day_statement)).mappings().all()

        return {
            "total_requests": total,
            "successful_requests": successful,
            "failed_requests": failed,
            "success_rate": successful / total * 100 if total else 0.0,
            "error_rate": failed / total * 100 if total else 0.0,
            "avg_latency_ms": float(row["avg_latency_ms"] or 0),
            "median_latency_ms": float(row["median_latency_ms"] or 0),
            "p95_latency_ms": float(row["p95_latency_ms"] or 0),
            "avg_time_to_first_token_ms": float(row["avg_ttft_ms"] or 0),
            "prompt_tokens": int(row["prompt_tokens"] or 0),
            "completion_tokens": int(row["completion_tokens"] or 0),
            "total_tokens": total_tokens,
            "avg_tokens_per_request": total_tokens / total if total else 0.0,
            "total_cost": total_cost,
            "avg_cost_per_request": total_cost / total if total else Decimal(0),
            "unique_users": int(row["unique_users"] or 0),
            "requests_by_model": [dict(item) for item in by_model],
            "errors_by_type": [dict(item) for item in by_error],
            "requests_by_day": [dict(item) for item in by_day],
        }

    async def models(self, filters: AnalyticsFilters) -> list[dict[str, Any]]:
        conditions = self._conditions(filters)
        statement = (
            select(
                LLMRequestEvent.model,
                func.count().label("requests"),
                func.count().filter(LLMRequestEvent.status == "success").label("successful"),
                func.count().filter(LLMRequestEvent.status == "error").label("failed"),
                func.avg(LLMRequestEvent.latency_ms).label("avg_latency_ms"),
                func.percentile_cont(0.95)
                .within_group(LLMRequestEvent.latency_ms)
                .label("p95_latency_ms"),
                func.coalesce(func.sum(LLMRequestEvent.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(LLMRequestEvent.total_cost), Decimal(0)).label(
                    "total_cost"
                ),
            )
            .where(*conditions)
            .group_by(LLMRequestEvent.model)
            .order_by(func.count().desc(), LLMRequestEvent.model)
        )
        rows = (await self._session.execute(statement)).mappings().all()
        result: list[dict[str, Any]] = []
        for row in rows:
            requests = int(row["requests"])
            cost = Decimal(row["total_cost"] or 0)
            result.append(
                {
                    "model": row["model"],
                    "requests": requests,
                    "success_rate": int(row["successful"] or 0) / requests * 100,
                    "error_rate": int(row["failed"] or 0) / requests * 100,
                    "avg_latency_ms": float(row["avg_latency_ms"] or 0),
                    "p95_latency_ms": float(row["p95_latency_ms"] or 0),
                    "total_tokens": int(row["total_tokens"] or 0),
                    "total_cost": cost,
                    "avg_cost_per_request": cost / requests,
                }
            )
        return result

    async def errors(self, filters: AnalyticsFilters) -> list[dict[str, Any]]:
        conditions = [*self._conditions(filters), LLMRequestEvent.status == "error"]
        total_statement = select(func.count()).where(*conditions)
        total = int((await self._session.execute(total_statement)).scalar_one() or 0)
        models = func.array_agg(distinct(LLMRequestEvent.model)).filter(
            LLMRequestEvent.model.is_not(None)
        )
        scenarios = func.array_agg(distinct(LLMRequestEvent.scenario)).filter(
            LLMRequestEvent.scenario.is_not(None)
        )
        statement = (
            select(
                LLMRequestEvent.error_type,
                func.count().label("count"),
                models.label("affected_models"),
                scenarios.label("affected_scenarios"),
            )
            .where(*conditions)
            .group_by(LLMRequestEvent.error_type)
            .order_by(func.count().desc())
        )
        rows = (await self._session.execute(statement)).mappings().all()
        return [
            {
                "error_type": row["error_type"] or "internal_proxy_error",
                "count": int(row["count"]),
                "share": int(row["count"]) / total * 100 if total else 0.0,
                "affected_models": sorted(row["affected_models"] or []),
                "affected_scenarios": sorted(row["affected_scenarios"] or []),
            }
            for row in rows
        ]

    async def _active_users(
        self, filters: AnalyticsFilters, end: datetime, days: int
    ) -> int:
        conditions = [
            *self._conditions(filters, include_dates=False),
            LLMRequestEvent.started_at >= end - timedelta(days=days),
            LLMRequestEvent.started_at < end,
            LLMRequestEvent.user_id_hash.is_not(None),
        ]
        statement = select(func.count(distinct(LLMRequestEvent.user_id_hash))).where(
            *conditions
        )
        return int((await self._session.execute(statement)).scalar_one() or 0)

    async def usage(self, filters: AnalyticsFilters, active_window_end: datetime) -> dict[str, Any]:
        conditions = self._conditions(filters)
        totals_statement = select(
            func.count().label("requests"),
            func.count(distinct(LLMRequestEvent.user_id_hash)).label("users"),
        ).where(*conditions)
        totals = (await self._session.execute(totals_statement)).mappings().one()
        requests = int(totals["requests"] or 0)
        users = int(totals["users"] or 0)

        async def breakdown(column: Any, key: str) -> list[dict[str, Any]]:
            statement = (
                select(column.label(key), func.count().label("requests"))
                .where(*conditions, column.is_not(None))
                .group_by(column)
                .order_by(func.count().desc(), column)
            )
            rows = (await self._session.execute(statement)).mappings().all()
            return [dict(row) for row in rows]

        return {
            "dau": await self._active_users(filters, active_window_end, 1),
            "wau": await self._active_users(filters, active_window_end, 7),
            "mau": await self._active_users(filters, active_window_end, 30),
            "requests_per_user": requests / users if users else 0.0,
            "requests_by_department": await breakdown(
                LLMRequestEvent.department, "department"
            ),
            "requests_by_scenario": await breakdown(LLMRequestEvent.scenario, "scenario"),
        }
