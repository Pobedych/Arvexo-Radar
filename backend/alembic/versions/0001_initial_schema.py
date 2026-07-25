"""initial schema: tenants, datasets, dataset_versions, records, record_chunks,
analysis_runs, analysis_jobs

Revision ID: 0001
Revises:
Create Date: 2026-07-24
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "tenants",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "datasets",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("source_filename_safe", sa.String(255), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_datasets_tenant_id", "datasets", ["tenant_id"])
    op.create_index("ix_datasets_checksum", "datasets", ["checksum"])

    op.create_table(
        "dataset_versions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", pg.UUID(as_uuid=True), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("schema_mapping", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("validation_summary", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("normalization_version", sa.String(30), nullable=False),
        sa.Column("masking_version", sa.String(30), nullable=False),
        sa.Column("storage_refs", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dataset_versions_dataset_id", "dataset_versions", ["dataset_id"])

    op.create_table(
        "records",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "dataset_version_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("dataset_versions.id"),
            nullable=False,
        ),
        sa.Column("external_request_id", sa.String(255), nullable=True),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("raw_storage_ref", sa.Text, nullable=False),
        sa.Column("masked_text", sa.Text, nullable=True),
        sa.Column("metadata_json", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("validation_status", sa.String(30), nullable=False),
        sa.Column("warnings", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("sanitized_hash", sa.String(64), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "dataset_version_id", "external_request_id", name="uq_record_external_id"
        ),
    )
    op.create_index("ix_records_dataset_version_id", "records", ["dataset_version_id"])

    op.create_table(
        "record_chunks",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("record_id", pg.UUID(as_uuid=True), sa.ForeignKey("records.id"), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("masked_text", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("embedding_model_version", sa.String(50), nullable=True),
        sa.Column("chunking_version", sa.String(30), nullable=False),
        sa.UniqueConstraint(
            "record_id", "position", "chunking_version", name="uq_chunk_position"
        ),
    )
    op.create_index("ix_record_chunks_record_id", "record_chunks", ["record_id"])

    op.create_table(
        "analysis_runs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column(
            "dataset_version_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("dataset_versions.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("stage", sa.String(30), nullable=True),
        sa.Column("config_snapshot", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("model_provenance", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analysis_runs_tenant_id", "analysis_runs", ["tenant_id"])

    op.create_table(
        "analysis_jobs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id", pg.UUID(as_uuid=True), sa.ForeignKey("analysis_runs.id"), nullable=False
        ),
        sa.Column("stage", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_owner", sa.String(100), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("safe_error", sa.String(500), nullable=True),
    )
    op.create_index("ix_analysis_jobs_run_id", "analysis_jobs", ["run_id"])


def downgrade() -> None:
    op.drop_table("analysis_jobs")
    op.drop_table("analysis_runs")
    op.drop_table("record_chunks")
    op.drop_table("records")
    op.drop_table("dataset_versions")
    op.drop_table("datasets")
    op.drop_table("tenants")
