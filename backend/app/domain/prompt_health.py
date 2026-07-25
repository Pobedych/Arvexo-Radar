"""Prompt-health and security finding rules (docs/11-dashboard.md section 9,
docs/16-security.md SEC-03).

A finding is a *potential* signal, never a proven incident or a guarantee
that masking caught everything (docs/16-security.md section 5) — severity
and masked_evidence must stay safe to render as-is in the UI/report.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

RULE_TOO_SHORT = "PH_TOO_SHORT"
RULE_TOO_LONG = "PH_TOO_LONG"
RULE_DUPLICATE = "PH_DUPLICATE"
RULE_SENSITIVE_DATA = "SEC_SENSITIVE_DATA"

TOO_SHORT_TOKENS = 3
TOO_LONG_TOKENS = 4000


@dataclass(frozen=True)
class RecordForHealthCheck:
    record_id: str
    masked_text: str
    token_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class FindingDraft:
    record_id: str | None
    rule_id: str
    type: str  # prompt_health | security
    severity: str  # low | medium | high
    masked_evidence: str | None
    metadata: dict


def evaluate_findings(records: list[RecordForHealthCheck]) -> list[FindingDraft]:
    findings: list[FindingDraft] = []
    text_counts = Counter(r.masked_text for r in records)

    for record in records:
        if record.token_count < TOO_SHORT_TOKENS:
            findings.append(
                FindingDraft(
                    record_id=record.record_id,
                    rule_id=RULE_TOO_SHORT,
                    type="prompt_health",
                    severity="low",
                    masked_evidence=record.masked_text[:200],
                    metadata={"token_count": record.token_count},
                )
            )
        if record.token_count > TOO_LONG_TOKENS:
            findings.append(
                FindingDraft(
                    record_id=record.record_id,
                    rule_id=RULE_TOO_LONG,
                    type="prompt_health",
                    severity="low",
                    masked_evidence=record.masked_text[:200],
                    metadata={"token_count": record.token_count},
                )
            )
        if text_counts[record.masked_text] > 1:
            findings.append(
                FindingDraft(
                    record_id=record.record_id,
                    rule_id=RULE_DUPLICATE,
                    type="prompt_health",
                    severity="low",
                    masked_evidence=record.masked_text[:200],
                    metadata={"duplicate_count": text_counts[record.masked_text]},
                )
            )
        if "sensitive_data_masked" in record.warnings:
            findings.append(
                FindingDraft(
                    record_id=record.record_id,
                    rule_id=RULE_SENSITIVE_DATA,
                    type="security",
                    severity="medium",
                    masked_evidence=record.masked_text[:200],
                    metadata={},
                )
            )

    return findings
