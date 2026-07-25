"""enterprise effectiveness, methodology, cost and knowledge adoption

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-25
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("llm_request_events", sa.Column("role", sa.String(150), nullable=True))
    op.add_column("llm_request_events", sa.Column("team", sa.String(255), nullable=True))
    op.add_column("llm_request_events", sa.Column("location", sa.String(255), nullable=True))
    op.add_column("llm_request_events", sa.Column("agent_id", sa.String(255), nullable=True))
    op.add_column("llm_request_events", sa.Column("scenario_id", sa.String(255), nullable=True))
    op.add_column(
        "llm_request_events",
        sa.Column("tool_calls", pg.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "llm_request_events", sa.Column("request_cost", sa.Numeric(24, 12), nullable=True)
    )
    op.create_index(
        "ix_llm_events_agent_started_at",
        "llm_request_events",
        ["agent_id", "started_at"],
    )
    op.create_index(
        "ix_llm_events_role_started_at",
        "llm_request_events",
        ["role", "started_at"],
    )

    op.add_column(
        "best_practices", sa.Column("department_origin", sa.String(150), nullable=True)
    )
    op.add_column(
        "best_practices",
        sa.Column("estimated_money_saved", sa.Numeric(18, 2), nullable=False, server_default="0"),
    )
    op.add_column("best_practices", sa.Column("approved_by", sa.String(255), nullable=True))
    op.add_column(
        "best_practices", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "best_practices",
        sa.Column("recommended_departments", pg.JSONB(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "tool_usages",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tool_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("agent_id", sa.String(255), nullable=False),
        sa.Column(
            "request_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("llm_request_events.request_id"),
            nullable=False,
        ),
        sa.Column("user_id_hash", sa.String(64), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_type", sa.String(50), nullable=True),
        sa.Column("latency_ms", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("latency_ms >= 0", name="ck_tool_usages_latency"),
    )
    op.create_index("ix_tool_usages_started_tool", "tool_usages", ["started_at", "tool_name"])
    op.create_index("ix_tool_usages_agent_started", "tool_usages", ["agent_id", "started_at"])

    op.create_table(
        "cost_components",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("period", sa.String(30), nullable=False),
        sa.Column("allocation_type", sa.String(50), nullable=False),
        sa.Column("agent_id", sa.String(255), nullable=True),
        sa.Column("model_id", sa.String(255), nullable=True),
        sa.Column("department_id", sa.String(255), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("is_estimated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("fixed_shares", pg.JSONB(), nullable=False, server_default="{}"),
        sa.CheckConstraint("amount >= 0", name="ck_cost_components_amount"),
        sa.CheckConstraint(
            "category IN ('token','inference','subscription','hardware_depreciation',"
            "'electricity','infrastructure','support','development_team','other')",
            name="ck_cost_components_category",
        ),
        sa.CheckConstraint(
            "allocation_type IN ('requests','tokens','inference_time','fixed_share','agent')",
            name="ck_cost_components_allocation",
        ),
    )
    op.create_index(
        "ix_cost_components_period", "cost_components", ["effective_from", "effective_to"]
    )

    op.create_table(
        "methodology_settings",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("average_monthly_fte_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("monthly_work_hours_per_fte", sa.Numeric(8, 2), nullable=False),
        sa.Column("include_development_team", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("electricity_price_per_kwh", sa.Numeric(12, 4), nullable=False),
        sa.Column("hardware_depreciation_months", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("calculation_period", sa.String(30), nullable=False, server_default="month"),
        sa.Column("profitability_thresholds", pg.JSONB(), nullable=False, server_default="{}"),
        sa.Column("best_practice_rules", pg.JSONB(), nullable=False, server_default="{}"),
        sa.UniqueConstraint("tenant_id", name="uq_methodology_tenant"),
        sa.CheckConstraint("average_monthly_fte_cost >= 0", name="ck_methodology_fte_cost"),
        sa.CheckConstraint("monthly_work_hours_per_fte > 0", name="ck_methodology_work_hours"),
        sa.CheckConstraint("hardware_depreciation_months > 0", name="ck_methodology_depreciation"),
    )

    op.create_table(
        "scenario_benchmarks",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scenario_id", sa.String(255), nullable=False),
        sa.Column("scenario_name", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255), nullable=False),
        sa.Column("baseline_minutes_without_ai", sa.Numeric(10, 2), nullable=False),
        sa.Column("actual_minutes_with_ai", sa.Numeric(10, 2), nullable=False),
        sa.Column("minutes_saved_per_task", sa.Numeric(10, 2), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("confidence_level", sa.Numeric(5, 2), nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_estimated", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("baseline_minutes_without_ai >= 0", name="ck_benchmark_baseline"),
        sa.CheckConstraint("actual_minutes_with_ai >= 0", name="ck_benchmark_actual"),
        sa.CheckConstraint("minutes_saved_per_task >= 0", name="ck_benchmark_saved"),
        sa.CheckConstraint("sample_size >= 0", name="ck_benchmark_sample"),
    )
    op.create_index(
        "ix_benchmarks_scenario_period",
        "scenario_benchmarks",
        ["scenario_id", "effective_from"],
    )

    op.create_table(
        "practice_adoptions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "practice_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("best_practices.id"),
            nullable=False,
        ),
        sa.Column("target_department", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="recommended"),
        sa.Column("recommended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_usage_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("time_saved_after_adoption", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("money_saved_after_adoption", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "practice_id", "target_department", name="uq_practice_adoption_target"
        ),
    )
    op.create_index(
        "ix_practice_adoptions_status", "practice_adoptions", ["practice_id", "status"]
    )


def downgrade() -> None:
    op.drop_table("practice_adoptions")
    op.drop_table("scenario_benchmarks")
    op.drop_table("methodology_settings")
    op.drop_table("cost_components")
    op.drop_table("tool_usages")
    for column in (
        "recommended_departments",
        "approved_at",
        "approved_by",
        "estimated_money_saved",
        "department_origin",
    ):
        op.drop_column("best_practices", column)
    op.drop_index("ix_llm_events_role_started_at", table_name="llm_request_events")
    op.drop_index("ix_llm_events_agent_started_at", table_name="llm_request_events")
    for column in (
        "request_cost",
        "tool_calls",
        "scenario_id",
        "agent_id",
        "location",
        "team",
        "role",
    ):
        op.drop_column("llm_request_events", column)
