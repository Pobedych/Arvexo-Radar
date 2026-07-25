"""Deterministic sensitive-data masking (docs/08-dataset.md section 7,
docs/10-ai-pipeline.md section 4).

Regex detectors are a best-effort signal, not a leakage guarantee
(docs/16-security.md section 5) — a finding is "potential", never "proven".
Placeholders are stable per-record (`[EMAIL_1]`, `[EMAIL_2]`, ...); the
raw-to-placeholder mapping is never persisted or returned.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?<!\w)(\+?\d[\d\-\s()]{8,}\d)(?!\w)")
# Common API key / token shapes: long high-entropy alnum runs, or provider-style
# prefixes (sk-, ghp_, AKIA...). Intentionally broad; false positives are safer
# than missed secrets for this MVP detector.
_SECRET_RE = re.compile(
    r"\b(?:sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}|[A-Za-z0-9_\-]{32,})\b"
)

_DETECTORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("EMAIL", _EMAIL_RE),
    ("SECRET", _SECRET_RE),
    ("PHONE", _PHONE_RE),
)


@dataclass(frozen=True)
class MaskingFinding:
    kind: str  # EMAIL | PHONE | SECRET
    placeholder: str


@dataclass(frozen=True)
class MaskingResult:
    masked_text: str
    findings: tuple[MaskingFinding, ...]


def mask_text(text: str) -> MaskingResult:
    findings: list[MaskingFinding] = []
    counters: dict[str, int] = {}
    result = text

    for kind, pattern in _DETECTORS:
        def _replace(match: re.Match[str], kind: str = kind) -> str:
            counters[kind] = counters.get(kind, 0) + 1
            placeholder = f"[{kind}_{counters[kind]}]"
            findings.append(MaskingFinding(kind=kind, placeholder=placeholder))
            return placeholder

        result = pattern.sub(_replace, result)

    return MaskingResult(masked_text=result, findings=tuple(findings))
