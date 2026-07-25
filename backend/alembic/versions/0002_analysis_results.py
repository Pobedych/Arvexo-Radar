"""analysis results: classifications, scenarios, scenario_members, findings,
insights, recommendations, reports; idempotency keys on analysis_runs

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-25
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analysis_runs", sa.Column("degradations", pg.JSONB, nullable=False, server_default="[]"))
    op.add_column("analysis_runs", sa.Column("idempotency_key", sa.String(255), nullable=True))
    op.create_unique_constraint(
        "uq_run_idempotency_key", "analysis_runs", ["dataset_version_id", "idempotency_key"]
    )

    op.create_table(
        "classifications",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", pg.UUID(as_uuid=True), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("record_id", pg.UUID(as_uuid=True), sa.ForeignKey("records.id"), nullable=False),
        sa.Column("category_id", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("evidence_refs", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("method_version", sa.String(30), nullable=False),
        sa.UniqueConstraint("run_id", "record_id", "category_id", name="uq_classification"),
    )
    op.create_index("ix_classifications_run_id", "classifications", ["run_id"])

    op.create_table(
        "scenarios",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", pg.UUID(as_uuid=True), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("cluster_label", sa.Integer, nullable=False),
        sa.Column("is_noise", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("typical_phrasings", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("share", sa.Float, nullable=False),
        sa.Column("quality", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("category_ids", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("provenance", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("generation_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("caveats", pg.JSONB, nullable=False, server_default="[]"),
    )
    op.create_index("ix_scenarios_run_id", "scenarios", ["run_id"])

    op.create_table(
        "scenario_members",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("scenario_id", pg.UUID(as_uuid=True), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("record_id", pg.UUID(as_uuid=True), sa.ForeignKey("records.id"), nullable=False),
        sa.Column("similarity", sa.Float, nullable=False),
        sa.Column("is_representative", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("selection_reason", sa.String(100), nullable=True),
    )
    op.create_index("ix_scenario_members_scenario_id", "scenario_members", ["scenario_id"])

    op.create_table(
        "findings",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", pg.UUID(as_uuid=True), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("record_id", pg.UUID(as_uuid=True), sa.ForeignKey("records.id"), nullable=True),
        sa.Column("rule_id", sa.String(100), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("masked_evidence", sa.Text, nullable=True),
        sa.Column("finding_metadata", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_findings_run_id", "findings", ["run_id"])

    op.create_table(
        "insights",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", pg.UUID(as_uuid=True), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("statement", sa.Text, nullable=False),
        sa.Column("evidence_refs", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("limitations", pg.JSONB, nullable=False, server_default="[]"),
    )
    op.create_index("ix_insights_run_id", "insights", ["run_id"])

    op.create_table(
        "recommendations",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", pg.UUID(as_uuid=True), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("insight_id", pg.UUID(as_uuid=True), sa.ForeignKey("insights.id"), nullable=True),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("priority_basis", sa.String(100), nullable=False),
        sa.Column("caveats", pg.JSONB, nullable=False, server_default="[]"),
    )
    op.create_index("ix_recommendations_run_id", "recommendations", ["run_id"])

    op.create_table(
        "reports",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", pg.UUID(as_uuid=True), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
        sa.Column("format", sa.String(10), nullable=False, server_default="pdf"),
        sa.Column("storage_ref", sa.Text, nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("safe_error", sa.String(500), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "idempotency_key", name="uq_report_idempotency_key"),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("recommendations")
    op.drop_table("insights")
    op.drop_table("findings")
    op.drop_table("scenario_members")
    op.drop_table("scenarios")
    op.drop_table("classifications")
    op.drop_constraint("uq_run_idempotency_key", "analysis_runs", type_="unique")
    op.drop_column("analysis_runs", "idempotency_key")
    op.drop_column("analysis_runs", "degradations")
