"""Core SQLAlchemy models for the Hackathon MVP slice.

Covers docs/14-database.md sections 3. Category taxonomy is a versioned
Python constant (app/domain/taxonomy.py), not its own table: v1 scope is a
single fixed taxonomy, so a table would only add an unused join without
letting anything vary yet.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    BestPracticeStatus,
    DatasetStatus,
    PracticeAdoptionStatus,
    RecordStatus,
    RunStage,
    RunStatus,
)
from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin


class Tenant(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(200))


class Dataset(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "datasets"
    __table_args__ = (Index("ix_datasets_tenant_id", "tenant_id"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    display_name: Mapped[str] = mapped_column(String(255))
    source_filename_safe: Mapped[str] = mapped_column(String(255))
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[DatasetStatus] = mapped_column(String(30), default=DatasetStatus.UPLOADED)
    created_by: Mapped[str] = mapped_column(String(255))

    versions: Mapped[list[DatasetVersion]] = relationship(back_populates="dataset")


class DatasetVersion(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "dataset_versions"

    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), index=True)
    schema_mapping: Mapped[dict] = mapped_column(JSONB, default=dict)
    validation_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    normalization_version: Mapped[str] = mapped_column(String(30))
    masking_version: Mapped[str] = mapped_column(String(30))
    storage_refs: Mapped[dict] = mapped_column(JSONB, default=dict)

    dataset: Mapped[Dataset] = relationship(back_populates="versions")
    records: Mapped[list[Record]] = relationship(back_populates="dataset_version")


class Record(UUIDPKMixin, Base):
    __tablename__ = "records"
    __table_args__ = (
        UniqueConstraint("dataset_version_id", "external_request_id", name="uq_record_external_id"),
        Index("ix_records_dataset_version_id", "dataset_version_id"),
    )

    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dataset_versions.id"), index=True
    )
    external_request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    row_number: Mapped[int] = mapped_column(Integer)
    raw_storage_ref: Mapped[str] = mapped_column(Text)
    masked_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validation_status: Mapped[RecordStatus] = mapped_column(String(30))
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list)
    sanitized_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    dataset_version: Mapped[DatasetVersion] = relationship(back_populates="records")
    chunks: Mapped[list[RecordChunk]] = relationship(back_populates="record")


class RecordChunk(UUIDPKMixin, Base):
    __tablename__ = "record_chunks"
    __table_args__ = (
        UniqueConstraint("record_id", "position", "chunking_version", name="uq_chunk_position"),
    )

    record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("records.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    masked_text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    embedding_model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    chunking_version: Mapped[str] = mapped_column(String(30))

    record: Mapped[Record] = relationship(back_populates="chunks")


class AnalysisRun(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        Index("ix_analysis_runs_tenant_id", "tenant_id"),
        UniqueConstraint(
            "dataset_version_id", "idempotency_key", name="uq_run_idempotency_key"
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dataset_versions.id"))
    status: Mapped[RunStatus] = mapped_column(String(30), default=RunStatus.QUEUED)
    stage: Mapped[RunStage | None] = mapped_column(String(30), nullable=True)
    config_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    model_provenance: Mapped[dict] = mapped_column(JSONB, default=dict)
    degradations: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[str] = mapped_column(String(255))
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)


class AnalysisJob(UUIDPKMixin, Base):
    __tablename__ = "analysis_jobs"
    __table_args__ = (Index("ix_analysis_jobs_run_id", "run_id"),)

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    stage: Mapped[RunStage] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lease_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    safe_error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Classification(UUIDPKMixin, Base):
    __tablename__ = "classifications"
    __table_args__ = (
        UniqueConstraint("run_id", "record_id", "category_id", name="uq_classification"),
        Index("ix_classifications_run_id", "run_id"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("records.id"), index=True)
    category_id: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    evidence_refs: Mapped[list[str]] = mapped_column(JSONB, default=list)
    method_version: Mapped[str] = mapped_column(String(30))


class Scenario(UUIDPKMixin, Base):
    __tablename__ = "scenarios"
    __table_args__ = (Index("ix_scenarios_run_id", "run_id"),)

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    cluster_label: Mapped[int] = mapped_column(Integer)
    is_noise: Mapped[bool] = mapped_column(default=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    typical_phrasings: Mapped[list[str]] = mapped_column(JSONB, default=list)
    size: Mapped[int] = mapped_column(Integer)
    share: Mapped[float] = mapped_column(Float)
    quality: Mapped[dict] = mapped_column(JSONB, default=dict)
    category_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)
    generation_status: Mapped[str] = mapped_column(String(30), default="pending")
    caveats: Mapped[list[str]] = mapped_column(JSONB, default=list)

    members: Mapped[list[ScenarioMember]] = relationship(back_populates="scenario")


class ScenarioMember(UUIDPKMixin, Base):
    __tablename__ = "scenario_members"
    __table_args__ = (Index("ix_scenario_members_scenario_id", "scenario_id"),)

    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenarios.id"), index=True)
    record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("records.id"), index=True)
    similarity: Mapped[float] = mapped_column(Float)
    is_representative: Mapped[bool] = mapped_column(default=False)
    selection_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    scenario: Mapped[Scenario] = relationship(back_populates="members")


class Finding(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "findings"
    __table_args__ = (Index("ix_findings_run_id", "run_id"),)

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    record_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("records.id"), nullable=True)
    rule_id: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(30))  # prompt_health | security
    severity: Mapped[str] = mapped_column(String(20))
    masked_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)


class Insight(UUIDPKMixin, Base):
    __tablename__ = "insights"
    __table_args__ = (Index("ix_insights_run_id", "run_id"),)

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    type: Mapped[str] = mapped_column(String(20))  # observation | hypothesis
    statement: Mapped[str] = mapped_column(Text)
    evidence_refs: Mapped[list[str]] = mapped_column(JSONB, default=list)
    confidence: Mapped[float] = mapped_column(Float)
    limitations: Mapped[list[str]] = mapped_column(JSONB, default=list)

    recommendations: Mapped[list[Recommendation]] = relationship(back_populates="insight")


class Recommendation(UUIDPKMixin, Base):
    __tablename__ = "recommendations"
    __table_args__ = (Index("ix_recommendations_run_id", "run_id"),)

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    insight_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("insights.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    priority_basis: Mapped[str] = mapped_column(String(100))
    caveats: Mapped[list[str]] = mapped_column(JSONB, default=list)

    insight: Mapped[Insight | None] = relationship(back_populates="recommendations")


class Report(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("run_id", "idempotency_key", name="uq_report_idempotency_key"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    format: Mapped[str] = mapped_column(String(10), default="pdf")
    storage_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    safe_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)


class LLMRequestEvent(Base):
    """Content-free technical telemetry for one proxied LLM request."""

    __tablename__ = "llm_request_events"
    __table_args__ = (
        CheckConstraint("status IN ('success', 'error')", name="ck_llm_events_status"),
        CheckConstraint(
            "error_type IS NULL OR error_type IN ("
            "'provider_error', 'timeout', 'rate_limit', 'authentication_error', "
            "'content_filter', 'tool_error', 'invalid_response', 'internal_proxy_error')",
            name="ck_llm_events_error_type",
        ),
        CheckConstraint("latency_ms >= 0", name="ck_llm_events_latency_nonnegative"),
        CheckConstraint(
            "time_to_first_token_ms IS NULL OR time_to_first_token_ms >= 0",
            name="ck_llm_events_ttft_nonnegative",
        ),
        CheckConstraint("messages_count >= 0", name="ck_llm_events_messages_nonnegative"),
        CheckConstraint(
            "input_characters >= 0", name="ck_llm_events_input_characters_nonnegative"
        ),
        Index("ix_llm_events_started_at_model", "started_at", "model"),
        Index("ix_llm_events_department_started_at", "department", "started_at"),
        Index("ix_llm_events_scenario_started_at", "scenario", "started_at"),
        Index("ix_llm_events_status_started_at", "status", "started_at"),
        Index("ix_llm_events_error_type_started_at", "error_type", "started_at"),
        Index("ix_llm_events_user_started_at", "user_id_hash", "started_at"),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    first_token_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    model: Mapped[str] = mapped_column(String(255))
    stream: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20))
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    latency_ms: Mapped[int] = mapped_column(BigInteger)
    time_to_first_token_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    messages_count: Mapped[int] = mapped_column(Integer)
    input_characters: Mapped[int] = mapped_column(BigInteger)
    prompt_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    input_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    output_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)
    currency: Mapped[str] = mapped_column(String(3))
    user_id_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    role: Mapped[str | None] = mapped_column(String(150), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scenario_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scenario: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_calls: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    request_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 12), nullable=True)


class ModelTariff(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "model_tariffs"
    __table_args__ = (
        CheckConstraint(
            "input_price_per_1m_tokens >= 0", name="ck_model_tariffs_input_price"
        ),
        CheckConstraint(
            "output_price_per_1m_tokens >= 0", name="ck_model_tariffs_output_price"
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="ck_model_tariffs_effective_interval",
        ),
        UniqueConstraint(
            "model_name", "currency", "effective_from", name="uq_model_tariff_effective"
        ),
        Index("ix_model_tariffs_lookup", "model_name", "effective_from", "effective_to"),
    )

    model_name: Mapped[str] = mapped_column(String(255))
    input_price_per_1m_tokens: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    output_price_per_1m_tokens: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    currency: Mapped[str] = mapped_column(String(3))
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BestPractice(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "best_practices"
    __table_args__ = (
        Index("ix_best_practices_tenant_status", "tenant_id", "status"),
        Index("ix_best_practices_tenant_impact", "tenant_id", "impact_score"),
        UniqueConstraint(
            "tenant_id", "source_scenario_id", name="uq_best_practice_source_scenario"
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    source_scenario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scenarios.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    short_description: Mapped[str] = mapped_column(Text)
    department: Mapped[str] = mapped_column(String(150))
    department_origin: Mapped[str | None] = mapped_column(String(150), nullable=True)
    scenario: Mapped[str] = mapped_column(String(200))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[BestPracticeStatus] = mapped_column(
        String(30), default=BestPracticeStatus.DETECTED
    )
    confidence_score: Mapped[float] = mapped_column(Float)
    impact_score: Mapped[float] = mapped_column(Float)
    adoption_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_time_saved: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_fte_saved: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_money_saved: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)

    recommendation: Mapped[str] = mapped_column(Text)
    user_count: Mapped[int] = mapped_column(Integer, default=0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    error_rate: Mapped[float] = mapped_column(Float, default=0.0)
    growth_rate: Mapped[float] = mapped_column(Float, default=0.0)
    departments: Mapped[list[str]] = mapped_column(JSONB, default=list)
    models: Mapped[list[str]] = mapped_column(JSONB, default=list)
    detection_evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recommended_departments: Mapped[list[str]] = mapped_column(JSONB, default=list)


class ToolUsage(UUIDPKMixin, Base):
    __tablename__ = "tool_usages"
    __table_args__ = (
        Index("ix_tool_usages_started_tool", "started_at", "tool_name"),
        Index("ix_tool_usages_agent_started", "agent_id", "started_at"),
    )

    tool_name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100))
    agent_id: Mapped[str] = mapped_column(String(255))
    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("llm_request_events.request_id"))
    user_id_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30))
    error_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latency_ms: Mapped[int] = mapped_column(BigInteger)


class CostComponent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "cost_components"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_cost_components_amount"),
        Index("ix_cost_components_period", "effective_from", "effective_to"),
    )

    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    period: Mapped[str] = mapped_column(String(30))
    allocation_type: Mapped[str] = mapped_column(String(50))
    agent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(255))
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    fixed_shares: Mapped[dict] = mapped_column(JSONB, default=dict)


class MethodologySettings(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "methodology_settings"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_methodology_tenant"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    average_monthly_fte_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    monthly_work_hours_per_fte: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    include_development_team: Mapped[bool] = mapped_column(Boolean, default=False)
    electricity_price_per_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    hardware_depreciation_months: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    calculation_period: Mapped[str] = mapped_column(String(30), default="month")
    profitability_thresholds: Mapped[dict] = mapped_column(JSONB, default=dict)
    best_practice_rules: Mapped[dict] = mapped_column(JSONB, default=dict)


class ScenarioBenchmark(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "scenario_benchmarks"
    __table_args__ = (Index("ix_benchmarks_scenario_period", "scenario_id", "effective_from"),)

    scenario_id: Mapped[str] = mapped_column(String(255))
    scenario_name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(255))
    baseline_minutes_without_ai: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    actual_minutes_with_ai: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    minutes_saved_per_task: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    source_type: Mapped[str] = mapped_column(String(50))
    sample_size: Mapped[int] = mapped_column(Integer)
    confidence_level: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PracticeAdoption(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "practice_adoptions"
    __table_args__ = (
        UniqueConstraint("practice_id", "target_department", name="uq_practice_adoption_target"),
        Index("ix_practice_adoptions_status", "practice_id", "status"),
    )

    practice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("best_practices.id"))
    target_department: Mapped[str] = mapped_column(String(255))
    status: Mapped[PracticeAdoptionStatus] = mapped_column(
        String(30), default=PracticeAdoptionStatus.RECOMMENDED
    )
    recommended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_usage_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    usages: Mapped[int] = mapped_column(Integer, default=0)
    time_saved_after_adoption: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    money_saved_after_adoption: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
