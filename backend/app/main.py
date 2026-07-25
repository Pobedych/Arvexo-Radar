from fastapi import FastAPI

from app.api.error_handlers import arvexo_error_handler, unhandled_error_handler
from app.api.routers import datasets, reports, runs, system
from app.domain.errors import ArvexoError

app = FastAPI(title="Arvexo Radar API", version="0.1.0")

app.add_exception_handler(ArvexoError, arvexo_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(system.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(runs.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
