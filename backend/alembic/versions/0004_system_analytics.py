"""system analytics telemetry and effective-dated model tariffs

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-25
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_tariffs",
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("input_price_per_1m_tokens", sa.Numeric(24, 12), nullable=False),
        sa.Column("output_price_per_1m_tokens", sa.Numeric(24, 12), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "input_price_per_1m_tokens >= 0", name="ck_model_tariffs_input_price"
        ),
        sa.CheckConstraint(
            "output_price_per_1m_tokens >= 0", name="ck_model_tariffs_output_price"
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="ck_model_tariffs_effective_interval",
        ),
        sa.UniqueConstraint(
            "model_name", "currency", "effective_from", name="uq_model_tariff_effective"
        ),
    )
    op.create_index(
        "ix_model_tariffs_lookup",
        "model_tariffs",
        ["model_name", "effective_from", "effective_to"],
    )

    op.create_table(
        "llm_request_events",
        sa.Column("request_id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_token_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model", sa.String(255), nullable=False),
        sa.Column("stream", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error_type", sa.String(50), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("latency_ms", sa.BigInteger(), nullable=False),
        sa.Column("time_to_first_token_ms", sa.BigInteger(), nullable=True),
        sa.Column("messages_count", sa.Integer(), nullable=False),
        sa.Column("input_characters", sa.BigInteger(), nullable=False),
        sa.Column("prompt_tokens", sa.BigInteger(), nullable=True),
        sa.Column("completion_tokens", sa.BigInteger(), nullable=True),
        sa.Column("total_tokens", sa.BigInteger(), nullable=True),
        sa.Column("input_cost", sa.Numeric(24, 12), nullable=True),
        sa.Column("output_cost", sa.Numeric(24, 12), nullable=True),
        sa.Column("total_cost", sa.Numeric(24, 12), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("user_id_hash", sa.String(64), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("scenario", sa.String(255), nullable=True),
        sa.CheckConstraint("status IN ('success', 'error')", name="ck_llm_events_status"),
        sa.CheckConstraint(
            "error_type IS NULL OR error_type IN ("
            "'provider_error', 'timeout', 'rate_limit', 'authentication_error', "
            "'content_filter', 'tool_error', 'invalid_response', 'internal_proxy_error')",
            name="ck_llm_events_error_type",
        ),
        sa.CheckConstraint("latency_ms >= 0", name="ck_llm_events_latency_nonnegative"),
        sa.CheckConstraint(
            "time_to_first_token_ms IS NULL OR time_to_first_token_ms >= 0",
            name="ck_llm_events_ttft_nonnegative",
        ),
        sa.CheckConstraint("messages_count >= 0", name="ck_llm_events_messages_nonnegative"),
        sa.CheckConstraint(
            "input_characters >= 0", name="ck_llm_events_input_characters_nonnegative"
        ),
    )
    op.create_index(
        "ix_llm_events_started_at_model", "llm_request_events", ["started_at", "model"]
    )
    op.create_index(
        "ix_llm_events_department_started_at",
        "llm_request_events",
        ["department", "started_at"],
    )
    op.create_index(
        "ix_llm_events_scenario_started_at",
        "llm_request_events",
        ["scenario", "started_at"],
    )
    op.create_index(
        "ix_llm_events_status_started_at", "llm_request_events", ["status", "started_at"]
    )
    op.create_index(
        "ix_llm_events_error_type_started_at",
        "llm_request_events",
        ["error_type", "started_at"],
    )
    op.create_index(
        "ix_llm_events_user_started_at",
        "llm_request_events",
        ["user_id_hash", "started_at"],
    )


def downgrade() -> None:
    op.drop_table("llm_request_events")
    op.drop_table("model_tariffs")
