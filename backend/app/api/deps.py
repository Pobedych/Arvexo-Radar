from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.create_analysis_run import CreateAnalysisRun
from app.application.create_dataset import CreateDataset
from app.application.generate_report import GenerateReport
from app.application.run_queries import RunQueries
from app.config import Settings, get_settings
from app.infrastructure.db.session import get_session
from app.infrastructure.storage import DatasetStorage, ReportStorage
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.dataset_repository import DatasetRepository


def get_dataset_storage(settings: Settings = Depends(get_settings)) -> DatasetStorage:
    return DatasetStorage(settings.storage_path)


def get_report_storage(settings: Settings = Depends(get_settings)) -> ReportStorage:
    return ReportStorage(settings.storage_path)


async def get_dataset_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[DatasetRepository]:
    yield DatasetRepository(session)


async def get_create_dataset_use_case(
    repository: DatasetRepository = Depends(get_dataset_repository),
    storage: DatasetStorage = Depends(get_dataset_storage),
    settings: Settings = Depends(get_settings),
) -> CreateDataset:
    return CreateDataset(repository, storage, settings)


async def get_analysis_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[AnalysisRepository]:
    yield AnalysisRepository(session)


async def get_create_analysis_run_use_case(
    dataset_repository: DatasetRepository = Depends(get_dataset_repository),
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository),
) -> CreateAnalysisRun:
    return CreateAnalysisRun(dataset_repository, analysis_repository)


async def get_run_queries(
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository),
) -> RunQueries:
    return RunQueries(analysis_repository)


async def get_generate_report_use_case(
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository),
    dataset_repository: DatasetRepository = Depends(get_dataset_repository),
    run_queries: RunQueries = Depends(get_run_queries),
    storage: ReportStorage = Depends(get_report_storage),
    settings: Settings = Depends(get_settings),
) -> GenerateReport:
    return GenerateReport(analysis_repository, dataset_repository, run_queries, storage, settings)


def get_current_principal() -> str:
    """Demo-mode principal (docs/16-security.md section 4).

    Production profile must fail closed without a configured auth adapter;
    that adapter does not exist yet, so this dependency is demo-mode only.
    """
    return "demo-user"
