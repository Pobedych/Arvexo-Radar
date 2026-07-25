"""CSV parsing and row-level validation for uploaded datasets.

Implements the canonical schema and validation codes V001-V009 from
docs/08-dataset.md sections 3 and 5. Pure domain logic: no FastAPI,
SQLAlchemy, or filesystem access, so it can be unit/property tested in
isolation and reused unchanged by the API path today and the worker job
later (docs/09-architecture.md ARCH-AC-02 spirit applied to this module too).

Token counting uses a whitespace-split heuristic. docs/10-ai-pipeline.md
section 3 requires a tokenizer matching the chosen model version once one is
selected; this placeholder must be replaced together with that decision, not
silently kept as the real count.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import RecordStatus, ValidationCode
from app.domain.masking import mask_text
from app.domain.normalization import normalize_text

CANONICAL_FIELDS = {
    "text",
    "request_id",
    "timestamp",
    "user_id",
    "team",
    "direction",
    "agent_id",
    "language",
    "metadata",
}
REQUIRED_FIELD = "text"
ALLOWED_DELIMITERS = (",", ";", "\t")


@dataclass(frozen=True)
class RowResult:
    row_number: int
    status: RecordStatus
    external_request_id: str | None
    masked_text: str | None
    token_count: int | None
    warnings: tuple[str, ...]
    rejection_code: str | None
    timestamp: datetime | None
    trend_eligible: bool
    metadata: dict[str, str]


@dataclass
class DatasetParseResult:
    accepted: int = 0
    accepted_with_warnings: int = 0
    rejected: int = 0
    dataset_rejection_code: str | None = None
    unknown_fields: tuple[str, ...] = ()
    conflicting_request_ids: tuple[str, ...] = ()
    rows: list[RowResult] = field(default_factory=list)
    schema_mapping: dict[str, str] = field(default_factory=dict)

    @property
    def is_dataset_rejected(self) -> bool:
        return self.dataset_rejection_code is not None

    @property
    def has_conflict(self) -> bool:
        return bool(self.conflicting_request_ids)

    def to_summary(self) -> dict:
        return {
            "accepted": self.accepted,
            "accepted_with_warnings": self.accepted_with_warnings,
            "rejected": self.rejected,
            "dataset_rejection_code": self.dataset_rejection_code,
            "unknown_fields": list(self.unknown_fields),
            "conflicting_request_ids": list(self.conflicting_request_ids),
        }


def _detect_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(ALLOWED_DELIMITERS))
        if dialect.delimiter in ALLOWED_DELIMITERS:
            return dialect.delimiter
    except csv.Error:
        pass
    return ","


def _parse_timestamp(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.strip())
    except ValueError:
        return None


def parse_and_validate(
    raw_bytes: bytes,
    *,
    max_row_chars: int,
) -> DatasetParseResult:
    result = DatasetParseResult()

    if not raw_bytes.strip():
        result.dataset_rejection_code = ValidationCode.V001_EMPTY_FILE.value
        return result

    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        result.dataset_rejection_code = ValidationCode.V004_INVALID_STRUCTURE.value
        return result

    delimiter = _detect_delimiter(text[:4096])

    try:
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        fieldnames = reader.fieldnames
    except csv.Error:
        result.dataset_rejection_code = ValidationCode.V004_INVALID_STRUCTURE.value
        return result

    if not fieldnames:
        result.dataset_rejection_code = ValidationCode.V002_MISSING_TEXT_MAPPING.value
        return result

    normalized_headers = {h: h.strip().lower() for h in fieldnames if h is not None}
    schema_mapping = {
        canonical: source
        for source, canonical in normalized_headers.items()
        if canonical in CANONICAL_FIELDS
    }
    result.schema_mapping = schema_mapping
    result.unknown_fields = tuple(
        h for h, canonical in normalized_headers.items() if canonical not in CANONICAL_FIELDS
    )

    if REQUIRED_FIELD not in schema_mapping:
        result.dataset_rejection_code = ValidationCode.V002_MISSING_TEXT_MAPPING.value
        return result

    text_source = schema_mapping[REQUIRED_FIELD]
    seen_request_ids: dict[str, str] = {}
    conflicts: set[str] = set()

    try:
        for row_number, raw_row in enumerate(reader, start=1):
            row_result = _validate_row(
                raw_row,
                row_number=row_number,
                text_source=text_source,
                schema_mapping=schema_mapping,
                max_row_chars=max_row_chars,
            )

            if row_result.external_request_id:
                rid = row_result.external_request_id
                fingerprint = row_result.masked_text or ""
                if rid in seen_request_ids and seen_request_ids[rid] != fingerprint:
                    conflicts.add(rid)
                seen_request_ids.setdefault(rid, fingerprint)

            result.rows.append(row_result)
            if row_result.status is RecordStatus.ACCEPTED:
                result.accepted += 1
            elif row_result.status is RecordStatus.ACCEPTED_WITH_WARNINGS:
                result.accepted_with_warnings += 1
            else:
                result.rejected += 1
    except csv.Error:
        result.dataset_rejection_code = ValidationCode.V004_INVALID_STRUCTURE.value
        return result

    result.conflicting_request_ids = tuple(sorted(conflicts))

    if result.accepted == 0 and result.accepted_with_warnings == 0:
        result.dataset_rejection_code = ValidationCode.V009_NO_VALID_ROWS.value

    return result


def _validate_row(
    raw_row: dict[str, str | None],
    *,
    row_number: int,
    text_source: str,
    schema_mapping: dict[str, str],
    max_row_chars: int,
) -> RowResult:
    warnings: list[str] = []

    raw_text = raw_row.get(text_source) or ""
    if not raw_text.strip():
        return RowResult(
            row_number=row_number,
            status=RecordStatus.REJECTED,
            external_request_id=None,
            masked_text=None,
            token_count=None,
            warnings=(),
            rejection_code=ValidationCode.V003_EMPTY_TEXT.value,
            timestamp=None,
            trend_eligible=False,
            metadata={},
        )

    if len(raw_text) > max_row_chars:
        return RowResult(
            row_number=row_number,
            status=RecordStatus.REJECTED,
            external_request_id=None,
            masked_text=None,
            token_count=None,
            warnings=(),
            rejection_code=ValidationCode.V007_ROW_TOO_LONG.value,
            timestamp=None,
            trend_eligible=False,
            metadata={},
        )

    normalized = normalize_text(raw_text)
    masking = mask_text(normalized)
    if masking.findings:
        warnings.append("sensitive_data_masked")

    external_request_id = None
    if "request_id" in schema_mapping:
        raw_id = raw_row.get(schema_mapping["request_id"])
        external_request_id = raw_id.strip() if raw_id else None

    timestamp: datetime | None = None
    trend_eligible = False
    if "timestamp" in schema_mapping:
        raw_ts = raw_row.get(schema_mapping["timestamp"])
        if raw_ts and raw_ts.strip():
            timestamp = _parse_timestamp(raw_ts)
            if timestamp is None:
                warnings.append("invalid_timestamp")
            else:
                trend_eligible = True

    metadata: dict[str, str] = {}
    for field_name in ("user_id", "team", "direction", "agent_id", "language"):
        if field_name in schema_mapping:
            value = raw_row.get(schema_mapping[field_name])
            if value and value.strip():
                metadata[field_name] = value.strip()

    status = RecordStatus.ACCEPTED_WITH_WARNINGS if warnings else RecordStatus.ACCEPTED
    token_count = len(normalized.split())

    return RowResult(
        row_number=row_number,
        status=status,
        external_request_id=external_request_id,
        masked_text=masking.masked_text,
        token_count=token_count,
        warnings=tuple(warnings),
        rejection_code=None,
        timestamp=timestamp,
        trend_eligible=trend_eligible,
        metadata=metadata,
    )
