from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_session

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    """Process liveness only, no dependency details (docs/15-api.md section 3)."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict:
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - readiness must degrade safely on any DB failure
        return {"status": "not_ready", "database": "unavailable"}
    return {"status": "ready", "database": "ok"}
