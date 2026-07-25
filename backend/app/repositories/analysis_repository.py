"""Analysis run repository: runs, jobs, and all pipeline result tables.

Every run/job/result lookup is tenant- or run-scoped (DB-AC-01, SEC-06).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import RecordStatus, RunStage, RunStatus
from app.infrastructure.db.models import (
    AnalysisJob,
    AnalysisRun,
    Classification,
    DatasetVersion,
    Finding,
    Insight,
    Recommendation,
    Record,
    Report,
    Scenario,
    ScenarioMember,
)


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- dataset / records -------------------------------------------------

    async def get_dataset_version(self, dataset_version_id: uuid.UUID) -> DatasetVersion | None:
        return await self._session.get(DatasetVersion, dataset_version_id)

    async def get_analyzable_records(self, dataset_version_id: uuid.UUID) -> list[Record]:
        stmt = select(Record).where(
            Record.dataset_version_id == dataset_version_id,
            Record.validation_status.in_(
                [RecordStatus.ACCEPTED, RecordStatus.ACCEPTED_WITH_WARNINGS]
            ),
        ).order_by(Record.row_number)
        return list((await self._session.execute(stmt)).scalars().all())

    # -- runs ---------------------------------------------------------------

    async def find_run_by_idempotency_key(
        self, dataset_version_id: uuid.UUID, key: str
    ) -> AnalysisRun | None:
        stmt = select(AnalysisRun).where(
            AnalysisRun.dataset_version_id == dataset_version_id,
            AnalysisRun.idempotency_key == key,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def create_run(
        self,
        *,
        tenant_id: uuid.UUID,
        dataset_version_id: uuid.UUID,
        config_snapshot: dict,
        created_by: str,
        idempotency_key: str | None,
    ) -> AnalysisRun:
        run = AnalysisRun(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            dataset_version_id=dataset_version_id,
            status=RunStatus.QUEUED,
            stage=None,
            config_snapshot=config_snapshot,
            model_provenance={},
            created_by=created_by,
            idempotency_key=idempotency_key,
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, *, tenant_id: uuid.UUID, run_id: uuid.UUID) -> AnalysisRun | None:
        stmt = select(AnalysisRun).where(
            AnalysisRun.tenant_id == tenant_id, AnalysisRun.id == run_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_run_by_id(self, run_id: uuid.UUID) -> AnalysisRun | None:
        return await self._session.get(AnalysisRun, run_id)

    async def commit(self) -> None:
        """Flush an interim state (e.g. `running`) so pollers see it before
        the pipeline finishes, instead of only ever observing queued/terminal."""
        await self._session.commit()

    # -- jobs -----------------------------------------------------------

    async def create_job(self, *, run_id: uuid.UUID, stage: RunStage) -> AnalysisJob:
        job = AnalysisJob(
            id=uuid.uuid4(),
            run_id=run_id,
            stage=stage,
            status="pending",
            attempts=0,
            available_at=datetime.now(UTC),
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def claim_next_job(self, *, worker_id: str, lease_seconds: int = 300) -> AnalysisJob | None:
        now = datetime.now(UTC)
        stmt = (
            select(AnalysisJob)
            .where(
                AnalysisJob.status == "pending",
                AnalysisJob.available_at <= now,
            )
            .order_by(AnalysisJob.available_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = (await self._session.execute(stmt)).scalar_one_or_none()
        if job is None:
            return None

        job.status = "running"
        job.attempts += 1
        job.lease_owner = worker_id
        job.lease_expires_at = now + timedelta(seconds=lease_seconds)
        job.heartbeat_at = now
        await self._session.flush()
        return job

    async def complete_job(self, job: AnalysisJob, *, safe_error: str | None = None) -> None:
        job.status = "failed" if safe_error else "completed"
        job.safe_error = safe_error
        await self._session.flush()

    # -- bulk result writes ----------------------------------------------

    async def bulk_create_classifications(self, classifications: list[Classification]) -> None:
        self._session.add_all(classifications)
        await self._session.flush()

    async def bulk_create_scenarios(self, scenarios: list[Scenario]) -> None:
        self._session.add_all(scenarios)
        await self._session.flush()

    async def bulk_create_scenario_members(self, members: list[ScenarioMember]) -> None:
        self._session.add_all(members)
        await self._session.flush()

    async def bulk_create_findings(self, findings: list[Finding]) -> None:
        self._session.add_all(findings)
        await self._session.flush()

    async def bulk_create_insights(self, insights: list[Insight]) -> None:
        self._session.add_all(insights)
        await self._session.flush()

    async def bulk_create_recommendations(self, recommendations: list[Recommendation]) -> None:
        self._session.add_all(recommendations)
        await self._session.flush()

    # -- result reads -------------------------------------------------------

    async def get_classifications(self, run_id: uuid.UUID) -> list[Classification]:
        stmt = select(Classification).where(Classification.run_id == run_id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_scenarios(self, run_id: uuid.UUID) -> list[Scenario]:
        stmt = select(Scenario).where(Scenario.run_id == run_id).order_by(Scenario.size.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_scenario(self, *, run_id: uuid.UUID, scenario_id: uuid.UUID) -> Scenario | None:
        stmt = select(Scenario).where(Scenario.run_id == run_id, Scenario.id == scenario_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_scenario_members(self, scenario_id: uuid.UUID) -> list[ScenarioMember]:
        stmt = select(ScenarioMember).where(ScenarioMember.scenario_id == scenario_id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_findings(self, run_id: uuid.UUID, *, finding_type: str | None = None) -> list[Finding]:
        stmt = select(Finding).where(Finding.run_id == run_id)
        if finding_type is not None:
            stmt = stmt.where(Finding.type == finding_type)
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_insights(self, run_id: uuid.UUID) -> list[Insight]:
        stmt = select(Insight).where(Insight.run_id == run_id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_recommendations(self, run_id: uuid.UUID) -> list[Recommendation]:
        stmt = select(Recommendation).where(Recommendation.run_id == run_id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_records_by_ids(self, record_ids: list[uuid.UUID]) -> dict[uuid.UUID, Record]:
        if not record_ids:
            return {}
        stmt = select(Record).where(Record.id.in_(record_ids))
        records = (await self._session.execute(stmt)).scalars().all()
        return {r.id: r for r in records}

    # -- reports ----------------------------------------------------------

    async def find_report_by_idempotency_key(self, run_id: uuid.UUID, key: str) -> Report | None:
        stmt = select(Report).where(Report.run_id == run_id, Report.idempotency_key == key)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def create_report(
        self,
        *,
        run_id: uuid.UUID,
        idempotency_key: str | None,
    ) -> Report:
        report = Report(
            id=uuid.uuid4(),
            run_id=run_id,
            status="queued",
            format="pdf",
            idempotency_key=idempotency_key,
        )
        self._session.add(report)
        await self._session.flush()
        return report

    async def get_report(self, report_id: uuid.UUID) -> Report | None:
        return await self._session.get(Report, report_id)

    async def mark_report_generated(
        self, report: Report, *, storage_ref: str, checksum: str
    ) -> None:
        report.status = "generated"
        report.storage_ref = storage_ref
        report.checksum = checksum
        report.generated_at = datetime.now(UTC)
        await self._session.flush()

    async def mark_report_failed(self, report: Report, *, safe_error: str) -> None:
        report.status = "failed"
        report.safe_error = safe_error
        await self._session.flush()
