from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_session

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    """Process liveness only, no dependency details (docs/15-api.md section 3)."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> JSONResponse:
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - readiness must degrade safely on any DB failure
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "unavailable"},
        )
    return JSONResponse(content={"status": "ready", "database": "ok"})
