"""BotHub adapter for bounded, evidence-backed structured generation."""

from __future__ import annotations

import ast
import asyncio
import json
import logging
import random
import re
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
    LLMErrorCode,
    LLMOperation,
    LLMProvenance,
    LLMProviderError,
    LLMResult,
)

_PROMPT_VERSION = "bothub-json-v2"
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
logger = logging.getLogger(__name__)

_OUTPUT_MODELS: dict[LLMOperation, type[BaseModel]] = {
    LLMOperation.SCENARIO_NAMING: ScenarioNamingOutput,
    LLMOperation.INSIGHT_WORDING: InsightWordingOutput,
    LLMOperation.RECOMMENDATION: RecommendationOutput,
}

_GENERATED_FIELDS: dict[LLMOperation, set[str]] = {
    LLMOperation.SCENARIO_NAMING: {"name", "description"},
    LLMOperation.INSIGHT_WORDING: {"statement", "limitations"},
    LLMOperation.RECOMMENDATION: {"action", "rationale", "priority_basis"},
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
    def __init__(
        self,
        *,
        code: LLMErrorCode,
        retryable: bool,
        safe_details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.retryable = retryable
        self.safe_details = dict(safe_details or {})


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
            attempt_headers = {
                **headers,
                "X-Idempotency-Key": f"{headers['X-Idempotency-Key']}:attempt:{attempt + 1}",
            }
            try:
                response = await client.post(
                    self._endpoint, headers=attempt_headers, json=payload
                )
                content, response_model, usage, finish_reason = self._extract_content(response)
                data = self._validate_output(
                    operation, evidence, content, finish_reason=finish_reason
                )
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
            except httpx.TimeoutException:
                failure = _AttemptError(code=LLMErrorCode.TIMEOUT, retryable=True)
            except httpx.TransportError:
                failure = _AttemptError(code=LLMErrorCode.TRANSPORT_ERROR, retryable=True)
            except _AttemptError as exc:
                failure = exc

            logger.warning(
                "BotHub generation attempt failed: operation=%s code=%s attempt=%d/%d "
                "retryable=%s details=%s",
                operation.value,
                failure.code.value,
                attempt + 1,
                self._max_retries + 1,
                failure.retryable,
                failure.safe_details,
            )

            if not failure.retryable or attempt == self._max_retries:
                raise LLMProviderError(
                    "BotHub generation failed.",
                    code=failure.code,
                    retryable=failure.retryable,
                    safe_details=failure.safe_details,
                ) from None
            if failure.code in {
                LLMErrorCode.INVALID_RESPONSE,
                LLMErrorCode.INVALID_JSON,
                LLMErrorCode.SCHEMA_VALIDATION_FAILED,
            }:
                payload = self._with_retry_instruction(payload)
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
            "return_schema": self._response_schema(operation),
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
    def _extract_content(
        response: httpx.Response,
    ) -> tuple[Any, str | None, dict[str, int], str | None]:
        if response.status_code >= 400:
            raise _AttemptError(
                code=LLMErrorCode.HTTP_ERROR,
                retryable=response.status_code in _RETRYABLE_STATUSES,
                safe_details={"status_code": response.status_code},
            )
        try:
            body = response.json()
        except ValueError:
            raise _AttemptError(code=LLMErrorCode.INVALID_RESPONSE, retryable=True) from None
        if not isinstance(body, dict):
            raise _AttemptError(code=LLMErrorCode.INVALID_RESPONSE, retryable=True)

        content: Any = None
        finish_reason: str | None = None
        choices = body.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            choice = choices[0]
            raw_finish_reason = choice.get("finish_reason") or choice.get("native_finish_reason")
            if isinstance(raw_finish_reason, str):
                finish_reason = raw_finish_reason[:80]
            message = choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if content in (None, ""):
                    tool_calls = message.get("tool_calls")
                    if isinstance(tool_calls, list) and tool_calls:
                        first_call = tool_calls[0]
                        if isinstance(first_call, dict):
                            function = first_call.get("function")
                            if isinstance(function, dict):
                                content = function.get("arguments")
            if content in (None, ""):
                content = choice.get("text")
        if content in (None, ""):
            content = body.get("output_text")

        content = BothubProvider._normalize_content(content)
        if content in (None, ""):
            raise _AttemptError(code=LLMErrorCode.INVALID_RESPONSE, retryable=True)

        model = body.get("model")
        raw_usage = body.get("usage", {})
        usage = (
            {
                key: value
                for key in ("prompt_tokens", "completion_tokens", "total_tokens")
                if isinstance((value := raw_usage.get(key)), int) and value >= 0
            }
            if isinstance(raw_usage, dict)
            else {}
        )
        return content, model if isinstance(model, str) and model else None, usage, finish_reason

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
        operation: LLMOperation,
        evidence: dict[str, Any],
        content: Any,
        *,
        finish_reason: str | None = None,
    ) -> dict[str, Any]:
        parsed = BothubProvider._parse_json_object(content, finish_reason=finish_reason)
        if operation is LLMOperation.INSIGHT_WORDING:
            parsed = {
                "type": str(evidence.get("type", "observation"))[:80],
                "confidence": evidence.get("confidence", 0.0),
                **parsed,
            }
        try:
            validated = _OUTPUT_MODELS[operation].model_validate(parsed)
        except ValidationError as exc:
            issues = [
                {
                    "type": str(issue.get("type", "validation_error")),
                    "loc": ".".join(str(part) for part in issue.get("loc", ())),
                }
                for issue in exc.errors(include_url=False, include_context=False, include_input=False)[
                    :10
                ]
            ]
            raise _AttemptError(
                code=LLMErrorCode.SCHEMA_VALIDATION_FAILED,
                retryable=True,
                safe_details={"issues": issues},
            ) from None

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
                raise _AttemptError(code=LLMErrorCode.INVALID_EVIDENCE, retryable=False)
        return data

    @staticmethod
    def _normalize_content(content: Any) -> Any:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, dict):
            for key in ("text", "content", "output_text", "json"):
                if key in content:
                    return BothubProvider._normalize_content(content[key])
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                normalized = BothubProvider._normalize_content(item)
                if isinstance(normalized, str) and normalized:
                    parts.append(normalized)
                elif isinstance(normalized, (dict, list)):
                    parts.append(json.dumps(normalized, ensure_ascii=False, separators=(",", ":")))
            return "".join(parts).strip()
        return None

    @staticmethod
    def _parse_json_object(
        content: Any, *, finish_reason: str | None = None
    ) -> dict[str, Any]:
        if isinstance(content, dict):
            return content
        if not isinstance(content, str):
            raise _AttemptError(code=LLMErrorCode.INVALID_JSON, retryable=True)

        normalized = content.strip().lstrip("\ufeff")
        if normalized.startswith("```"):
            lines = normalized.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                normalized = "\n".join(lines[1:-1]).strip()

        candidates = [normalized]
        candidates.extend(normalized[index:] for index, char in enumerate(normalized) if char == "{")
        decoder = json.JSONDecoder()
        for candidate in candidates:
            try:
                parsed, _ = decoder.raw_decode(candidate.lstrip())
                if isinstance(parsed, str):
                    parsed = json.loads(parsed)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                continue

        for candidate in BothubProvider._balanced_object_candidates(normalized):
            repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
            for value in (candidate, repaired):
                try:
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, dict):
                        return parsed
                except (SyntaxError, ValueError, TypeError):
                    continue

        details = {"finish_reason": finish_reason} if finish_reason else {}
        raise _AttemptError(
            code=LLMErrorCode.INVALID_JSON,
            retryable=True,
            safe_details=details,
        ) from None

    @staticmethod
    def _balanced_object_candidates(text: str) -> list[str]:
        candidates: list[str] = []
        for start, char in enumerate(text):
            if char != "{":
                continue
            depth = 0
            quote: str | None = None
            escaped = False
            for index in range(start, len(text)):
                current = text[index]
                if quote is not None:
                    if escaped:
                        escaped = False
                    elif current == "\\":
                        escaped = True
                    elif current == quote:
                        quote = None
                    continue
                if current in {'"', "'"}:
                    quote = current
                elif current == "{":
                    depth += 1
                elif current == "}":
                    depth -= 1
                    if depth == 0:
                        candidates.append(text[start : index + 1])
                        break
        return candidates

    @staticmethod
    def _compact_schema(schema: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "type",
            "properties",
            "required",
            "additionalProperties",
            "items",
            "minLength",
            "maxLength",
            "minimum",
            "maximum",
            "maxItems",
        }

        def compact(value: Any) -> Any:
            if isinstance(value, dict):
                result: dict[str, Any] = {}
                for key, item in value.items():
                    if key not in allowed:
                        continue
                    if key == "properties" and isinstance(item, dict):
                        result[key] = {name: compact(field) for name, field in item.items()}
                    else:
                        result[key] = compact(item)
                return result
            if isinstance(value, list):
                return [compact(item) for item in value]
            return value

        return compact(schema)

    @staticmethod
    def _response_schema(operation: LLMOperation) -> dict[str, Any]:
        schema = BothubProvider._compact_schema(_OUTPUT_MODELS[operation].model_json_schema())
        generated_fields = _GENERATED_FIELDS[operation]
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            schema["properties"] = {
                name: value for name, value in properties.items() if name in generated_fields
            }
        required = schema.get("required", [])
        if isinstance(required, list):
            schema["required"] = [name for name in required if name in generated_fields]
        return schema

    @staticmethod
    def _with_retry_instruction(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            **payload,
            "messages": [
                *payload["messages"],
                {
                    "role": "user",
                    "content": (
                        "The previous response could not be parsed. Return exactly one JSON "
                        "object matching return_schema, with no markdown or commentary."
                    ),
                },
            ],
        }

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
