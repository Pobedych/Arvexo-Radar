import pytest

from app.infrastructure.providers.mock_provider import MockProvider
from app.services.llm_provider import LLMOperation


@pytest.mark.asyncio
async def test_scenario_naming_uses_only_given_evidence() -> None:
    provider = MockProvider()
    evidence = {
        "cluster_id": "c1",
        "typical_phrasings": ["Собери сводку писем"],
        "evidence_refs": ["record:1"],
    }

    result = await provider.generate(
        operation=LLMOperation.SCENARIO_NAMING,
        schema_version="v1",
        evidence=evidence,
        locale="ru-RU",
        idempotency_key="test-key",
    )

    assert result.data["evidence_refs"] == evidence["evidence_refs"]
    assert result.data["typical_phrasings"] == evidence["typical_phrasings"]
    assert result.provenance.provider == "mock"
