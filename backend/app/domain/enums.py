"""Shared enums for dataset processing and analysis run state machines.

Values follow docs/08-dataset.md (validation codes) and
docs/09-architecture.md section 7 (run state model). Kept as plain
`str, Enum` so they serialize cleanly through Pydantic and SQLAlchemy without
importing either from the domain layer.
"""

from __future__ import annotations

from enum import Enum


class RecordStatus(str, Enum):
    ACCEPTED = "accepted"
    ACCEPTED_WITH_WARNINGS = "accepted_with_warnings"
    REJECTED = "rejected"


class ValidationCode(str, Enum):
    V001_EMPTY_FILE = "V001"
    V002_MISSING_TEXT_MAPPING = "V002"
    V003_EMPTY_TEXT = "V003"
    V004_INVALID_STRUCTURE = "V004"
    V005_INVALID_TIMESTAMP = "V005"
    V006_DUPLICATE_REQUEST_ID = "V006"
    V007_ROW_TOO_LONG = "V007"
    V008_UNKNOWN_FIELDS = "V008"
    V009_NO_VALID_ROWS = "V009"


class DatasetStatus(str, Enum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    VALIDATED = "validated"
    REJECTED = "rejected"
    CONFLICT = "conflict"


class RunStage(str, Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    NORMALIZING = "normalizing"
    MASKING = "masking"
    EMBEDDING = "embedding"
    CLASSIFYING = "classifying"
    CLUSTERING = "clustering"
    GENERATING = "generating"
    INSIGHTS = "insights"
    COMPLETED = "completed"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    DEGRADED = "degraded"
    FAILED = "failed"
    CANCELLED = "cancelled"
