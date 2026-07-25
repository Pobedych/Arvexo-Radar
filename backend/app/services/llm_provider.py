"""LLM provider port.

Domain/application code depends only on this Protocol, never on a concrete
SDK, per docs/09-architecture.md (ARCH-AC-02) and docs/10-ai-pipeline.md
section 9. Concrete adapters live under app/infrastructure/providers/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class LLMOperation(str, Enum):
    SCENARIO_NAMING = "scenario_naming"
    INSIGHT_WORDING = "insight_wording"
    RECOMMENDATION = "recommendation"


class LLMErrorCode(str, Enum):
    """Safe, provider-agnostic failure categories exposed in run degradations."""

    PROVIDER_UNAVAILABLE = "LLM_PROVIDER_UNAVAILABLE"
    TIMEOUT = "LLM_TIMEOUT"
    TRANSPORT_ERROR = "LLM_TRANSPORT_ERROR"
    HTTP_ERROR = "LLM_HTTP_ERROR"
    INVALID_RESPONSE = "LLM_INVALID_RESPONSE"
    INVALID_JSON = "LLM_INVALID_JSON"
    SCHEMA_VALIDATION_FAILED = "LLM_SCHEMA_VALIDATION_FAILED"
    INVALID_EVIDENCE = "LLM_INVALID_EVIDENCE"


@dataclass(frozen=True)
class LLMProvenance:
    provider: str
    model: str
    prompt_version: str
    schema_version: str


@dataclass(frozen=True)
class LLMResult:
    data: dict[str, Any]
    provenance: LLMProvenance
    degraded: bool = False
    usage: dict[str, int] = field(default_factory=dict)


class LLMProviderError(Exception):
    """Raised by adapters on unrecoverable provider failure.

    Caught by application services, which must fall back to a `degraded`
    run state rather than propagate raw provider errors (docs/10-ai-pipeline.md
    section 12).
    """

    def __init__(
        self,
        message: str,
        *,
        code: LLMErrorCode = LLMErrorCode.PROVIDER_UNAVAILABLE,
        retryable: bool = False,
        safe_details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.safe_details = dict(safe_details or {})


class LLMProvider(Protocol):
    """Every implementation must validate its own output against the schema
    for `operation`/`schema_version` before returning (AI-AC-02)."""

    async def generate(
        self,
        *,
        operation: LLMOperation,
        schema_version: str,
        evidence: dict[str, Any],
        locale: str,
        idempotency_key: str,
    ) -> LLMResult: ...
