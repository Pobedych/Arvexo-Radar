"""Core SQLAlchemy models for the Hackathon MVP slice.

Covers docs/14-database.md sections 3. Category taxonomy is a versioned
Python constant (app/domain/taxonomy.py), not its own table: v1 scope is a
single fixed taxonomy, so a table would only add an unused join without
letting anything vary yet.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import DatasetStatus, RecordStatus, RunStage, RunStatus
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
