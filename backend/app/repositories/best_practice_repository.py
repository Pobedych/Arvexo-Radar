from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import BestPracticeStatus, PracticeAdoptionStatus
from app.infrastructure.db.models import BestPractice, PracticeAdoption


class BestPracticeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, practice: BestPractice) -> BestPractice:
        self._session.add(practice)
        await self._session.flush()
        return practice

    async def existing_scenario_ids(
        self, *, tenant_id: uuid.UUID, scenario_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        if not scenario_ids:
            return set()
        stmt = select(BestPractice.source_scenario_id).where(
            BestPractice.tenant_id == tenant_id,
            BestPractice.source_scenario_id.in_(scenario_ids),
        )
        return {value for value in (await self._session.execute(stmt)).scalars() if value}

    async def list(
        self,
        *,
        tenant_id: uuid.UUID,
        status: BestPracticeStatus | None = None,
        department: str | None = None,
        model: str | None = None,
        min_impact_score: float | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[BestPractice], int]:
        filters = [BestPractice.tenant_id == tenant_id]
        if status is not None:
            filters.append(BestPractice.status == status)
        if department:
            filters.append(BestPractice.departments.contains([department]))
        if model:
            filters.append(BestPractice.models.contains([model]))
        if min_impact_score is not None:
            filters.append(BestPractice.impact_score >= min_impact_score)

        total_stmt = select(func.count()).select_from(BestPractice).where(*filters)
        total = int((await self._session.execute(total_stmt)).scalar_one())
        stmt = (
            select(BestPractice)
            .where(*filters)
            .order_by(BestPractice.impact_score.desc(), BestPractice.detected_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list((await self._session.execute(stmt)).scalars().all())
        return items, total

    async def get(
        self, *, tenant_id: uuid.UUID, practice_id: uuid.UUID
    ) -> BestPractice | None:
        stmt = select(BestPractice).where(
            BestPractice.tenant_id == tenant_id,
            BestPractice.id == practice_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def set_status(
        self,
        practice: BestPractice,
        status: BestPracticeStatus,
        *,
        actor: str | None = None,
    ) -> None:
        practice.status = status
        if status == BestPracticeStatus.APPROVED:
            practice.approved_by = actor
            practice.approved_at = datetime.now(UTC)
        await self._session.flush()

    async def approve(self, practice: BestPractice, actor: str | None = None) -> None:
        await self.set_status(practice, BestPracticeStatus.APPROVED, actor=actor)

    async def publish(self, practice: BestPractice) -> None:
        practice.status = BestPracticeStatus.PUBLISHED
        practice.published_at = datetime.now(UTC)
        await self._session.flush()

    async def recommend(
        self, practice: BestPractice, departments: list[str]
    ) -> None:
        practice.status = BestPracticeStatus.SCALING
        practice.recommended_departments = sorted(
            set((practice.recommended_departments or []) + departments)
        )
        await self._session.flush()

    async def list_adoptions(self, practice_id: uuid.UUID) -> list[PracticeAdoption]:
        statement = (
            select(PracticeAdoption)
            .where(PracticeAdoption.practice_id == practice_id)
            .order_by(PracticeAdoption.recommended_at.desc())
        )
        return list((await self._session.execute(statement)).scalars().all())

    async def upsert_adoption(
        self,
        *,
        practice_id: uuid.UUID,
        target_department: str,
        status: PracticeAdoptionStatus,
        active_users: int,
        usages: int,
        time_saved_after_adoption,
        money_saved_after_adoption,
        owner: str | None,
        comment: str | None,
    ) -> PracticeAdoption:
        statement = select(PracticeAdoption).where(
            PracticeAdoption.practice_id == practice_id,
            PracticeAdoption.target_department == target_department,
        )
        adoption = (await self._session.execute(statement)).scalar_one_or_none()
        now = datetime.now(UTC)
        if adoption is None:
            adoption = PracticeAdoption(
                practice_id=practice_id,
                target_department=target_department,
                status=status,
                recommended_at=now,
            )
            self._session.add(adoption)
        adoption.status = status
        adoption.active_users = active_users
        adoption.usages = usages
        adoption.time_saved_after_adoption = time_saved_after_adoption
        adoption.money_saved_after_adoption = money_saved_after_adoption
        adoption.owner = owner
        adoption.comment = comment
        if status in {
            PracticeAdoptionStatus.ACCEPTED,
            PracticeAdoptionStatus.PILOT,
            PracticeAdoptionStatus.ADOPTED,
        } and adoption.accepted_at is None:
            adoption.accepted_at = now
        if usages > 0 and adoption.first_usage_at is None:
            adoption.first_usage_at = now
        await self._session.flush()
        return adoption

    async def commit(self) -> None:
        await self._session.commit()
