from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import arvexo_error_handler, unhandled_error_handler
from app.api.routers import (
    analytics,
    best_practices,
    datasets,
    methodology,
    proxy,
    reports,
    runs,
    system,
)
from app.config import get_settings
from app.domain.errors import ArvexoError

app = FastAPI(title="Arvexo Radar API", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_exception_handler(ArvexoError, arvexo_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(system.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(runs.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(best_practices.router, prefix="/api")
app.include_router(proxy.router)
app.include_router(analytics.router, prefix="/api/analytics")
app.include_router(methodology.router, prefix="/api")
