import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.application.run_queries import RunQueries, _model_from_record_text


class DashboardRepository:
    def __init__(self) -> None:
        self.version = SimpleNamespace(
            validation_summary={"accepted": 1, "accepted_with_warnings": 2, "rejected": 1}
        )
        self.records = [
            SimpleNamespace(
                id=uuid.uuid4(),
                timestamp=datetime(2026, 5, 1, 11, tzinfo=UTC),
                warnings=[],
                metadata_json={
                    "team": "Legal",
                    "direction": "Product",
                    "agent_id": "sql-bot",
                    "language": "ru",
                },
                masked_text='{"model":"Qwen2.5-Coder-32B","messages":[]}',
            ),
            SimpleNamespace(
                id=uuid.uuid4(),
                timestamp=datetime(2026, 5, 1, 14, tzinfo=UTC),
                warnings=["sensitive_data_masked"],
                metadata_json={
                    "team": "Legal",
                    "direction": "Product",
                    "agent_id": "sql-bot",
                    "language": "ru",
                },
                masked_text='{"model":"Qwen2.5-Coder-32B","messages":[]}',
            ),
            SimpleNamespace(
                id=uuid.uuid4(),
                timestamp=None,
                warnings=["invalid_timestamp"],
                metadata_json={},
                masked_text="plain text",
            ),
        ]
        self.findings = [
            SimpleNamespace(record_id=self.records[0].id, severity="medium", type="security"),
            SimpleNamespace(record_id=self.records[0].id, severity="low", type="prompt_health"),
        ]

    async def get_dataset_version(self, dataset_version_id):
        return self.version

    async def get_analyzable_records(self, dataset_version_id):
        return self.records

    async def get_findings(self, run_id, finding_type=None):
        return self.findings


def test_model_is_read_from_request_payload() -> None:
    assert _model_from_record_text('{"model":"GPT-4.1-mini"}') == "GPT-4.1-mini"
    assert _model_from_record_text("not json") is None


def test_dashboard_metrics_reconcile_events_records_and_quality() -> None:
    repository = DashboardRepository()
    queries = RunQueries(repository)  # type: ignore[arg-type]
    run = SimpleNamespace(id=uuid.uuid4(), dataset_version_id=uuid.uuid4())

    result = asyncio.run(queries.dashboard_metrics(run, total_records=3))

    assert result["data_quality"]["total_rows"] == 4
    assert result["data_quality"]["warning_counts"]["invalid_timestamp"] == 1
    assert result["activity"]["valid_timestamp_records"] == 2
    assert result["segments"]["team"][0]["value"] == "Legal"
    assert result["segments"]["team"][-1]["is_missing"] is True
    assert result["risk_summary"]["total_findings"] == 2
    assert result["risk_summary"]["affected_records"] == 1
    assert result["risk_summary"]["affected_share"] == 1 / 3
