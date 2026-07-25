from __future__ import annotations

import json

import httpx
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.infrastructure.providers.bothub_provider import BothubProvider
from app.infrastructure.providers.factory import build_llm_provider
from app.services.llm_provider import LLMErrorCode, LLMOperation, LLMProviderError


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "llm_provider_mode": "bothub",
        "bothub_api_key": "test-secret",
        "bothub_base_url": "https://openai.bothub.chat/v1",
        "bothub_model": "gemini-2.5-flash",
        "llm_max_retries": 2,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def _completion(content: str, *, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        json={
            "model": "gemini-2.5-flash",
            "choices": [{"message": {"role": "assistant", "content": content}}],
            "usage": {"prompt_tokens": 91, "completion_tokens": 37, "total_tokens": 128},
        },
    )


async def _no_sleep(_: float) -> None:
    return None


@pytest.mark.asyncio
async def test_scenario_output_is_validated_bounded_and_keeps_local_evidence() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return _completion(
            json.dumps(
                {
                    "name": "Сводки переписки",
                    "description": "Пользователи кратко суммируют переписку.",
                    "typical_phrasings": ["invented"],
                    "evidence_refs": ["invented"],
                    "caveats": [],
                },
                ensure_ascii=False,
            )
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = BothubProvider(
            _settings(llm_max_samples=2, llm_max_sample_chars=100), client=client
        )
        result = await provider.generate(
            operation=LLMOperation.SCENARIO_NAMING,
            schema_version="v1",
            evidence={
                "cluster_id": "c1",
                "typical_phrasings": ["а" * 180, "второй", "третий"],
                "evidence_refs": ["scenario:1"],
            },
            locale="ru-RU",
            idempotency_key="run:scenario:1",
        )

    assert result.data["evidence_refs"] == ["scenario:1"]
    assert result.data["typical_phrasings"] == [f"{'а' * 99}…", "второй"]
    assert result.usage["total_tokens"] == 128
    assert captured["max_tokens"] == 320
    prompt = json.loads(captured["messages"][1]["content"])
    assert "output_schema" not in prompt
    assert len(prompt["evidence"]["typical_phrasings"]) == 2


@pytest.mark.asyncio
async def test_invalid_json_is_retried_once() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return _completion("not-json")
        return _completion(
            json.dumps(
                {
                    "action": "Проверить процесс.",
                    "rationale": "Инсайт показывает повторяемый сценарий.",
                    "linked_insight_ids": [],
                    "priority_basis": "usage_share",
                    "caveats": [],
                },
                ensure_ascii=False,
            )
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = BothubProvider(_settings(), client=client, sleep=_no_sleep)
        result = await provider.generate(
            operation=LLMOperation.RECOMMENDATION,
            schema_version="v1",
            evidence={
                "statement": "Сценарий встречается часто.",
                "linked_insight_ids": ["insight:1"],
            },
            locale="ru-RU",
            idempotency_key="run:recommendation:1",
        )

    assert calls == 2
    assert result.data["linked_insight_ids"] == ["insight:1"]


@pytest.mark.asyncio
async def test_authentication_error_is_not_retried_or_exposed() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(401, json={"error": {"message": "contains provider details"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = BothubProvider(_settings(), client=client, sleep=_no_sleep)
        with pytest.raises(LLMProviderError, match="BotHub generation failed") as exc_info:
            await provider.generate(
                operation=LLMOperation.SCENARIO_NAMING,
                schema_version="v1",
                evidence={"typical_phrasings": [], "evidence_refs": ["scenario:1"]},
                locale="ru-RU",
                idempotency_key="run:scenario:1",
            )

    assert calls == 1
    assert exc_info.value.code is LLMErrorCode.HTTP_ERROR
    assert exc_info.value.safe_details == {"status_code": 401}
    assert exc_info.value.retryable is False
    assert "provider details" not in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "expected_code", "expected_issue"),
    [
        ("not-json", LLMErrorCode.INVALID_JSON, None),
        (
            json.dumps({"name": "Без обязательного описания"}, ensure_ascii=False),
            LLMErrorCode.SCHEMA_VALIDATION_FAILED,
            {"type": "missing", "loc": "description"},
        ),
    ],
)
async def test_structured_output_failures_have_safe_diagnostic_codes(
    content: str,
    expected_code: LLMErrorCode,
    expected_issue: dict[str, str] | None,
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: _completion(content))
    ) as client:
        provider = BothubProvider(_settings(llm_max_retries=0), client=client)
        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate(
                operation=LLMOperation.SCENARIO_NAMING,
                schema_version="v1",
                evidence={"typical_phrasings": ["пример"], "evidence_refs": ["scenario:1"]},
                locale="ru-RU",
                idempotency_key="run:scenario:diagnostic",
            )

    assert exc_info.value.code is expected_code
    if expected_issue is None:
        assert exc_info.value.safe_details == {}
    else:
        assert expected_issue in exc_info.value.safe_details["issues"]
    assert content not in str(exc_info.value)


@pytest.mark.asyncio
async def test_timeout_has_distinct_diagnostic_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("secret timeout detail", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = BothubProvider(_settings(llm_max_retries=0), client=client)
        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate(
                operation=LLMOperation.SCENARIO_NAMING,
                schema_version="v1",
                evidence={"typical_phrasings": [], "evidence_refs": ["scenario:1"]},
                locale="ru-RU",
                idempotency_key="run:scenario:timeout",
            )

    assert exc_info.value.code is LLMErrorCode.TIMEOUT
    assert exc_info.value.retryable is True
    assert exc_info.value.safe_details == {}
    assert "secret timeout detail" not in str(exc_info.value)


def test_bothub_mode_requires_secret_and_factory_builds_adapter() -> None:
    with pytest.raises(ValidationError, match="ARVEXO_BOTHUB_API_KEY"):
        Settings(_env_file=None, llm_provider_mode="bothub", bothub_api_key=None)

    assert isinstance(build_llm_provider(_settings()), BothubProvider)
