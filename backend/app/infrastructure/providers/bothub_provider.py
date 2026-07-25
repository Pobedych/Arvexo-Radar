"""BotHub adapter for bounded, evidence-backed structured generation."""

from __future__ import annotations

import asyncio
import json
import random
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.schemas.llm import (
    InsightWordingOutput,
    RecommendationOutput,
    ScenarioNamingOutput,
)
from app.services.llm_provider import (
    LLMOperation,
    LLMProvenance,
    LLMProviderError,
    LLMResult,
)

_PROMPT_VERSION = "bothub-json-v1"
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}

_OUTPUT_MODELS: dict[LLMOperation, type[BaseModel]] = {
    LLMOperation.SCENARIO_NAMING: ScenarioNamingOutput,
    LLMOperation.INSIGHT_WORDING: InsightWordingOutput,
    LLMOperation.RECOMMENDATION: RecommendationOutput,
}

_OUTPUT_TEMPLATES = {
    LLMOperation.SCENARIO_NAMING: {
        "name": "short name",
        "description": "one sentence",
        "typical_phrasings": [],
        "evidence_refs": [],
        "caveats": [],
    },
    LLMOperation.INSIGHT_WORDING: {
        "type": "type",
        "statement": "one sentence",
        "evidence_refs": [],
        "confidence": 0.0,
        "limitations": [],
    },
    LLMOperation.RECOMMENDATION: {
        "action": "one action",
        "rationale": "one sentence",
        "linked_insight_ids": [],
        "priority_basis": "evidence basis",
        "caveats": [],
    },
}

_OPERATION_INSTRUCTIONS = {
    LLMOperation.SCENARIO_NAMING: (
        "Give the scenario a concise name and a factual one-sentence summary. "
        "Do not add use cases, outcomes, people, organizations, or metrics absent from evidence."
    ),
    LLMOperation.INSIGHT_WORDING: (
        "Rewrite the supplied aggregate insight clearly without changing its meaning, "
        "confidence, limitations, or evidence references."
    ),
    LLMOperation.RECOMMENDATION: (
        "Suggest one practical next action justified only by the supplied aggregate insight. "
        "Do not claim ROI, business outcomes, or causality absent from evidence."
    ),
}


class _AttemptError(Exception):
    def __init__(self, *, retryable: bool) -> None:
        self.retryable = retryable


class BothubProvider:
    """OpenAI-compatible BotHub Chat Completions adapter.

    The adapter never logs provider payloads or response bodies. It validates
    every model response and restores evidence identifiers from local input so
    an LLM cannot invent provenance.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        secret = settings.bothub_api_key
        if secret is None or not secret.get_secret_value().strip():
            raise ValueError("BotHub API key is required")

        base_url = settings.bothub_base_url.rstrip("/")
        self._endpoint = (
            base_url if base_url.endswith("/chat/completions") else f"{base_url}/chat/completions"
        )
        self._api_key = secret.get_secret_value().strip()
        self._model = settings.bothub_model
        self._timeout = settings.llm_timeout_seconds
        self._max_retries = settings.llm_max_retries
        self._max_output_tokens = settings.llm_max_output_tokens
        self._max_samples = settings.llm_max_samples
        self._max_sample_chars = settings.llm_max_sample_chars
        self._client = client
        self._sleep = sleep

    async def generate(
        self,
        *,
        operation: LLMOperation,
        schema_version: str,
        evidence: dict[str, Any],
        locale: str,
        idempotency_key: str,
    ) -> LLMResult:
        output_model = _OUTPUT_MODELS.get(operation)
        if output_model is None:  # pragma: no cover - exhaustive by enum
            raise ValueError(f"Unsupported operation: {operation}")

        bounded_evidence = self._bound_evidence(operation, evidence)
        payload = self._build_payload(
            operation=operation,
            evidence=bounded_evidence,
            locale=locale,
        )
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Idempotency-Key": idempotency_key,
        }

        if self._client is not None:
            return await self._generate_with_client(
                self._client, operation, schema_version, bounded_evidence, payload, headers
            )

        async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout)) as client:
            return await self._generate_with_client(
                client, operation, schema_version, bounded_evidence, payload, headers
            )

    async def _generate_with_client(
        self,
        client: httpx.AsyncClient,
        operation: LLMOperation,
        schema_version: str,
        evidence: dict[str, Any],
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> LLMResult:
        for attempt in range(self._max_retries + 1):
            try:
                response = await client.post(self._endpoint, headers=headers, json=payload)
                content, response_model, usage = self._extract_content(response)
                data = self._validate_output(operation, evidence, content)
                return LLMResult(
                    data=data,
                    provenance=LLMProvenance(
                        provider="bothub",
                        model=response_model or self._model,
                        prompt_version=_PROMPT_VERSION,
                        schema_version=schema_version,
                    ),
                    usage=usage,
                )
            except (httpx.TimeoutException, httpx.TransportError):
                failure = _AttemptError(retryable=True)
            except _AttemptError as exc:
                failure = exc

            if not failure.retryable or attempt == self._max_retries:
                raise LLMProviderError(
                    "BotHub generation failed.", retryable=failure.retryable
                ) from None
            await self._sleep(self._retry_delay(attempt))

        raise AssertionError("unreachable")  # pragma: no cover

    def _build_payload(
        self,
        *,
        operation: LLMOperation,
        evidence: dict[str, Any],
        locale: str,
    ) -> dict[str, Any]:
        request = {
            "task": _OPERATION_INSTRUCTIONS[operation],
            "language": locale,
            "evidence": evidence,
            "return": _OUTPUT_TEMPLATES[operation],
        }
        return {
            "model": self._model,
            "temperature": 0.1,
            "max_tokens": self._max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "JSON only. Use evidence only. Never invent facts.",
                },
                {
                    "role": "user",
                    "content": json.dumps(request, ensure_ascii=False, separators=(",", ":")),
                },
            ],
        }

    @staticmethod
    def _extract_content(response: httpx.Response) -> tuple[str, str | None, dict[str, int]]:
        if response.status_code >= 400:
            raise _AttemptError(retryable=response.status_code in _RETRYABLE_STATUSES)
        try:
            body = response.json()
            choices = body["choices"]
            content = choices[0]["message"]["content"]
            model = body.get("model")
            raw_usage = body.get("usage", {})
        except (ValueError, KeyError, IndexError, TypeError):
            raise _AttemptError(retryable=True) from None
        if not isinstance(content, str) or not content.strip():
            raise _AttemptError(retryable=True)
        usage = (
            {
                key: value
                for key in ("prompt_tokens", "completion_tokens", "total_tokens")
                if isinstance((value := raw_usage.get(key)), int) and value >= 0
            }
            if isinstance(raw_usage, dict)
            else {}
        )
        return content, model if isinstance(model, str) and model else None, usage

    def _bound_evidence(self, operation: LLMOperation, evidence: dict[str, Any]) -> dict[str, Any]:
        if operation is LLMOperation.SCENARIO_NAMING:
            samples = self._string_list(evidence.get("typical_phrasings"), limit=self._max_samples)
            return {
                "cluster_id": self._truncate(evidence.get("cluster_id"), 80),
                "typical_phrasings": [
                    self._truncate(sample, self._max_sample_chars) for sample in samples
                ],
                "evidence_refs": self._string_list(evidence.get("evidence_refs"), limit=10),
            }
        if operation is LLMOperation.INSIGHT_WORDING:
            return {
                "type": self._truncate(evidence.get("type"), 80),
                "statement": self._truncate(evidence.get("statement"), 800),
                "evidence_refs": self._string_list(evidence.get("evidence_refs"), limit=10),
                "confidence": evidence.get("confidence", 0.0),
                "limitations": [
                    self._truncate(item, 200)
                    for item in self._string_list(evidence.get("limitations"), limit=3)
                ],
            }
        return {
            "type": self._truncate(evidence.get("type"), 80),
            "statement": self._truncate(evidence.get("statement"), 800),
            "evidence_refs": self._string_list(evidence.get("evidence_refs"), limit=10),
            "confidence": evidence.get("confidence", 0.0),
            "limitations": [
                self._truncate(item, 200)
                for item in self._string_list(evidence.get("limitations"), limit=3)
            ],
            "linked_insight_ids": self._string_list(evidence.get("linked_insight_ids"), limit=3),
        }

    @staticmethod
    def _validate_output(
        operation: LLMOperation, evidence: dict[str, Any], content: str
    ) -> dict[str, Any]:
        normalized = content.strip()
        if normalized.startswith("```"):
            lines = normalized.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                normalized = "\n".join(lines[1:-1])
        try:
            parsed = json.loads(normalized)
            validated = _OUTPUT_MODELS[operation].model_validate(parsed)
        except (json.JSONDecodeError, ValidationError, TypeError):
            raise _AttemptError(retryable=True) from None

        data = validated.model_dump()
        if operation is LLMOperation.SCENARIO_NAMING:
            data["typical_phrasings"] = BothubProvider._string_list(
                evidence.get("typical_phrasings"), limit=5
            )
            data["evidence_refs"] = BothubProvider._string_list(
                evidence.get("evidence_refs"), limit=100
            )
        elif operation is LLMOperation.INSIGHT_WORDING:
            data["type"] = str(evidence.get("type", data["type"]))[:80]
            data["evidence_refs"] = BothubProvider._string_list(
                evidence.get("evidence_refs"), limit=100
            )
            if isinstance(evidence.get("confidence"), (int, float)):
                data["confidence"] = min(1.0, max(0.0, float(evidence["confidence"])))
        elif operation is LLMOperation.RECOMMENDATION:
            data["linked_insight_ids"] = BothubProvider._string_list(
                evidence.get("linked_insight_ids"), limit=20
            )
            if not data["linked_insight_ids"]:
                raise _AttemptError(retryable=False)
        return data

    @staticmethod
    def _string_list(value: Any, *, limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value[:limit] if isinstance(item, str)]

    @staticmethod
    def _truncate(value: Any, limit: int) -> str:
        text = value if isinstance(value, str) else str(value or "")
        return text if len(text) <= limit else f"{text[: limit - 1]}…"

    @staticmethod
    def _retry_delay(attempt: int) -> float:
        return min(0.5 * (2**attempt), 4.0) + random.uniform(0, 0.25)
