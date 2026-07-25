"""Deterministic text normalization (docs/08-dataset.md section 6).

Only reversible, meaning-preserving transforms are applied: Unicode NFC,
CRLF/CR -> LF, removal of NUL/control characters, and trimming outer
whitespace. Never translates, truncates, or otherwise changes meaning.
"""

from __future__ import annotations

import unicodedata

_DISALLOWED_CONTROL_CHARS = {chr(c) for c in range(0x20) if c not in (0x09, 0x0A)}


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "".join(ch for ch in normalized if ch not in _DISALLOWED_CONTROL_CHARS)
    return normalized.strip()
