"""best practices and knowledge discovery

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-25
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "best_practices",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column(
            "source_scenario_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("scenarios.id"),
            nullable=True,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("short_description", sa.Text, nullable=False),
        sa.Column("department", sa.String(150), nullable=False),
        sa.Column("scenario", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="detected"),
        sa.Column("confidence_score", sa.Float, nullable=False),
        sa.Column("impact_score", sa.Float, nullable=False),
        sa.Column("adoption_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("estimated_time_saved", sa.Float, nullable=False, server_default="0"),
        sa.Column("estimated_fte_saved", sa.Float, nullable=False, server_default="0"),
        sa.Column("tags", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("recommendation", sa.Text, nullable=False),
        sa.Column("user_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("usage_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("average_rating", sa.Float, nullable=True),
        sa.Column("success_rate", sa.Float, nullable=False, server_default="0"),
        sa.Column("error_rate", sa.Float, nullable=False, server_default="0"),
        sa.Column("growth_rate", sa.Float, nullable=False, server_default="0"),
        sa.Column("departments", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("models", pg.JSONB, nullable=False, server_default="[]"),
        sa.Column("detection_evidence", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "tenant_id", "source_scenario_id", name="uq_best_practice_source_scenario"
        ),
    )
    op.create_index(
        "ix_best_practices_tenant_status", "best_practices", ["tenant_id", "status"]
    )
    op.create_index(
        "ix_best_practices_tenant_impact", "best_practices", ["tenant_id", "impact_score"]
    )


def downgrade() -> None:
    op.drop_table("best_practices")
