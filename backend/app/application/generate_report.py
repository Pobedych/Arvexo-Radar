"""GenerateReport use case (docs/11-dashboard.md section 14,
docs/15-api.md reports endpoints).

Generation is only allowed from a terminal analytics state (`completed` or
`degraded`); a still-running run has no stable result set to report on.
Rendering failure marks the report `failed` with a safe error rather than
raising past the caller, so `POST .../reports` still returns 202 and the
client learns the outcome via `GET /reports/{id}`.
"""

from __future__ import annotations

import hashlib
import uuid

from app.application.run_queries import RunQueries
from app.config import Settings
from app.domain.errors import ReportGenerationError, RunNotFoundError, RunStateError
from app.infrastructure.db.models import Report
from app.infrastructure.reports.pdf_report import (
    ReportCategoryRow,
    ReportContent,
    ReportInsightRow,
    ReportRecommendationRow,
    ReportScenarioRow,
    render_report_pdf,
)
from app.infrastructure.storage import ReportStorage
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.dataset_repository import DatasetRepository

TERMINAL_STATUSES = ("completed", "degraded")


class GenerateReport:
    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        dataset_repository: DatasetRepository,
        run_queries: RunQueries,
        storage: ReportStorage,
        settings: Settings,
    ) -> None:
        self._analysis = analysis_repository
        self._datasets = dataset_repository
        self._queries = run_queries
        self._storage = storage
        self._settings = settings

    async def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        run_id: uuid.UUID,
        idempotency_key: str | None,
    ) -> Report:
        run = await self._analysis.get_run(tenant_id=tenant_id, run_id=run_id)
        if run is None:
            raise RunNotFoundError("Run not found.", details={})

        if run.status not in TERMINAL_STATUSES:
            raise RunStateError(
                "Report generation requires a completed or degraded run.",
                details={"status": run.status},
            )

        if idempotency_key:
            existing = await self._analysis.find_report_by_idempotency_key(run_id, idempotency_key)
            if existing is not None:
                return existing

        report = await self._analysis.create_report(run_id=run_id, idempotency_key=idempotency_key)

        version = await self._datasets.get_version(run.dataset_version_id)
        dataset = await self._datasets.get_dataset_by_id(version.dataset_id)
        total_records = version.validation_summary.get("accepted", 0) + version.validation_summary.get(
            "accepted_with_warnings", 0
        )

        overview = await self._queries.overview(
            run, dataset_id=dataset.id, total_records=total_records
        )

        content = ReportContent(
            dataset_name=dataset.display_name,
            run_id=str(run.id),
            status=run.status,
            generated_at=report.created_at.isoformat() if report.created_at else "",
            total_records=total_records,
            top_categories=[
                ReportCategoryRow(c["name"], c["count"], c["share"]) for c in overview["top_categories"]
            ],
            top_scenarios=[
                ReportScenarioRow(s["name"] or "—", s["description"], s["size"], s["share"])
                for s in overview["top_scenarios"]
            ],
            insights=[
                ReportInsightRow(i["type"], i["statement"], i["confidence"])
                for i in overview["insights"]
            ],
            recommendations=[
                ReportRecommendationRow(r["action"], r["rationale"]) for r in overview["recommendations"]
            ],
            limitations=overview["limitations"],
            degradation_notes=[
                f"{d['code']}: {', '.join(d['affected'])}" for d in overview["degradations"]
            ],
        )

        try:
            pdf_bytes = render_report_pdf(
                content,
                font_regular_path=self._settings.report_font_regular_path,
                font_bold_path=self._settings.report_font_bold_path,
            )
        except ReportGenerationError as exc:
            await self._analysis.mark_report_failed(report, safe_error=exc.code)
            return report

        checksum = hashlib.sha256(pdf_bytes).hexdigest()
        storage_ref = self._storage.save_pdf(report.id, pdf_bytes)
        await self._analysis.mark_report_generated(report, storage_ref=storage_ref, checksum=checksum)
        return report
