from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.infrastructure.db.models import LLMRequestEvent
from app.infrastructure.db.session import AsyncSessionLocal
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.proxy import ChatCompletionRequest, RadarMetadata

ErrorType = Literal[
    "provider_error",
    "timeout",
    "rate_limit",
    "authentication_error",
    "content_filter",
    "tool_error",
    "invalid_response",
    "internal_proxy_error",
]

MILLION = Decimal(1_000_000)
MAX_SSE_EVENT_BYTES = 1_000_000


class InvalidProviderResponse(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TokenUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(slots=True)
class TelemetryContext:
    request_id: uuid.UUID
    started_at: datetime
    model: str
    stream: bool
    messages_count: int
    input_characters: int
    user_id_hash: str | None = None
    role: str | None = None
    department: str | None = None
    team: str | None = None
    location: str | None = None
    agent_id: str | None = None
    scenario_id: str | None = None
    scenario: str | None = None
    tool_calls: list[str] = field(default_factory=list)
    first_token_at: datetime | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    finalized: bool = False


def utc_now() -> datetime:
    return datetime.now(UTC)


def milliseconds_between(start: datetime, end: datetime) -> int:
    return max(0, int((end - start).total_seconds() * 1000))


def hash_user_id(user_id: str | None, salt: str) -> str | None:
    if not user_id:
        return None
    digest = hashlib.sha256()
    digest.update(salt.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(user_id.encode("utf-8"))
    return digest.hexdigest()


def _count_strings(value: Any) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, list):
        return sum(_count_strings(item) for item in value)
    if isinstance(value, dict):
        return sum(_count_strings(item) for item in value.values())
    return 0


def count_input_characters(request: ChatCompletionRequest) -> int:
    return sum(_count_strings(message.content) for message in request.messages)


def extract_usage(payload: Any) -> TokenUsage:
    if not isinstance(payload, dict) or not isinstance(payload.get("usage"), dict):
        return TokenUsage()
    usage = payload["usage"]

    def token(name: str) -> int | None:
        value = usage.get(name)
        return value if isinstance(value, int) and value >= 0 else None

    prompt = token("prompt_tokens")
    completion = token("completion_tokens")
    total = token("total_tokens")
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion
    return TokenUsage(prompt, completion, total)


def calculate_costs(
    usage: TokenUsage,
    input_price_per_1m_tokens: Decimal,
    output_price_per_1m_tokens: Decimal,
) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    input_cost = (
        Decimal(usage.prompt_tokens) / MILLION * input_price_per_1m_tokens
        if usage.prompt_tokens is not None
        else None
    )
    output_cost = (
        Decimal(usage.completion_tokens) / MILLION * output_price_per_1m_tokens
        if usage.completion_tokens is not None
        else None
    )
    total_cost = input_cost + output_cost if input_cost is not None and output_cost is not None else None
    return input_cost, output_cost, total_cost


def _payload_text(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False).lower()
    except (TypeError, ValueError):
        return ""


def classify_http_error(status_code: int, payload: Any = None) -> ErrorType:
    text = _payload_text(payload)
    if status_code in {401, 403}:
        return "authentication_error"
    if status_code == 429:
        return "rate_limit"
    if "content_filter" in text or "content policy" in text or "safety" in text:
        return "content_filter"
    if "tool_error" in text or "tool execution" in text or "function_call" in text:
        return "tool_error"
    return "provider_error"


def classify_exception(exc: BaseException) -> ErrorType:
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, (InvalidProviderResponse, json.JSONDecodeError)):
        return "invalid_response"
    if isinstance(exc, httpx.HTTPError):
        return "provider_error"
    name = type(exc).__name__.lower()
    if "tool" in name:
        return "tool_error"
    return "internal_proxy_error"


def safe_error_message(error_type: ErrorType, http_status: int | None = None) -> str:
    messages = {
        "provider_error": "The upstream LLM provider returned an error.",
        "timeout": "The upstream LLM provider timed out.",
        "rate_limit": "The upstream LLM provider rate limit was exceeded.",
        "authentication_error": "The upstream LLM provider rejected authentication.",
        "content_filter": "The upstream LLM provider blocked the request by content policy.",
        "tool_error": "A model tool call failed.",
        "invalid_response": "The upstream LLM provider returned an invalid response.",
        "internal_proxy_error": "The proxy failed while processing the request.",
    }
    message = messages[error_type]
    return f"{message} HTTP {http_status}." if http_status is not None else message


def response_has_content_filter(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    choices = payload.get("choices")
    return isinstance(choices, list) and any(
        isinstance(choice, dict) and choice.get("finish_reason") == "content_filter"
        for choice in choices
    )


class SSEUsageParser:
    """Incrementally parses OpenAI SSE frames without retaining response text."""

    def __init__(self) -> None:
        self._buffer = b""
        self.usage = TokenUsage()
        self.content_filtered = False

    def feed(self, chunk: bytes) -> None:
        self._buffer += chunk.replace(b"\r\n", b"\n")
        while b"\n\n" in self._buffer:
            raw_event, self._buffer = self._buffer.split(b"\n\n", 1)
            self._consume_event(raw_event)
        if len(self._buffer) > MAX_SSE_EVENT_BYTES:
            raise InvalidProviderResponse("Provider SSE data frame exceeds the size limit")

    def finish(self) -> None:
        if self._buffer.strip():
            self._consume_event(self._buffer)
        self._buffer = b""

    def _consume_event(self, raw_event: bytes) -> None:
        if len(raw_event) > MAX_SSE_EVENT_BYTES:
            raise InvalidProviderResponse("Provider SSE data frame exceeds the size limit")
        data_lines = [line[5:].strip() for line in raw_event.split(b"\n") if line.startswith(b"data:")]
        if not data_lines:
            return
        data = b"\n".join(data_lines)
        if data == b"[DONE]":
            return
        try:
            payload = json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidProviderResponse("Invalid JSON in provider SSE data frame") from exc
        usage = extract_usage(payload)
        if any(value is not None for value in (usage.prompt_tokens, usage.completion_tokens, usage.total_tokens)):
            self.usage = usage
        if response_has_content_filter(payload):
            self.content_filtered = True


class TelemetryRecorder:
    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory

    def start(
        self,
        request: ChatCompletionRequest,
        metadata: RadarMetadata,
        *,
        started_at: datetime | None = None,
    ) -> TelemetryContext:
        return TelemetryContext(
            request_id=uuid.uuid4(),
            started_at=started_at or utc_now(),
            model=request.model,
            stream=request.stream,
            messages_count=len(request.messages),
            input_characters=count_input_characters(request),
            user_id_hash=hash_user_id(
                metadata.user_id, self._settings.analytics_user_hash_salt
            ),
            role=metadata.role,
            department=metadata.department,
            team=metadata.team,
            location=metadata.location,
            agent_id=metadata.agent_id,
            scenario_id=metadata.scenario_id,
            scenario=metadata.scenario,
            tool_calls=metadata.tool_calls,
        )

    @staticmethod
    def mark_first_token(context: TelemetryContext, at: datetime | None = None) -> None:
        if context.first_token_at is None:
            context.first_token_at = at or utc_now()

    async def finalize(
        self,
        context: TelemetryContext,
        *,
        status: Literal["success", "error"],
        http_status: int | None,
        usage: TokenUsage | None = None,
        error_type: ErrorType | None = None,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        if context.finalized:
            return
        completed = completed_at or utc_now()
        observed_usage = usage or context.usage
        input_cost: Decimal | None = None
        output_cost: Decimal | None = None
        total_cost: Decimal | None = None

        async with self._session_factory() as session:
            repository = AnalyticsRepository(session)
            tariff = await repository.find_tariff(
                context.model, context.started_at, self._settings.analytics_currency
            )
            if tariff is not None:
                input_cost, output_cost, total_cost = calculate_costs(
                    observed_usage,
                    Decimal(tariff.input_price_per_1m_tokens),
                    Decimal(tariff.output_price_per_1m_tokens),
                )
            event = LLMRequestEvent(
                request_id=context.request_id,
                started_at=context.started_at,
                first_token_at=context.first_token_at,
                completed_at=completed,
                model=context.model,
                stream=context.stream,
                status=status,
                http_status=http_status,
                error_type=error_type,
                error_message=error_message[:1000] if error_message else None,
                latency_ms=milliseconds_between(context.started_at, completed),
                time_to_first_token_ms=(
                    milliseconds_between(context.started_at, context.first_token_at)
                    if context.first_token_at is not None
                    else None
                ),
                messages_count=context.messages_count,
                input_characters=context.input_characters,
                prompt_tokens=observed_usage.prompt_tokens,
                completion_tokens=observed_usage.completion_tokens,
                total_tokens=observed_usage.total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                currency=self._settings.analytics_currency,
                user_id_hash=context.user_id_hash,
                role=context.role,
                department=context.department,
                team=context.team,
                location=context.location,
                agent_id=context.agent_id,
                scenario_id=context.scenario_id,
                scenario=context.scenario,
                tool_calls=[{"name": name} for name in context.tool_calls],
                request_cost=total_cost,
            )
            await repository.add_event(event)
            await session.commit()
        context.finalized = True
