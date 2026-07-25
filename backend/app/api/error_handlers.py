from __future__ import annotations

import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from app.domain.errors import ArvexoError


async def arvexo_error_handler(request: Request, exc: ArvexoError) -> JSONResponse:
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status,
        headers={"X-Correlation-ID": correlation_id},
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "retryable": exc.retryable,
                "details": exc.details,
                "correlation_id": correlation_id,
            }
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    return JSONResponse(
        status_code=500,
        headers={"X-Correlation-ID": correlation_id},
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Unexpected error occurred.",
                "retryable": False,
                "details": {},
                "correlation_id": correlation_id,
            }
        },
    )
