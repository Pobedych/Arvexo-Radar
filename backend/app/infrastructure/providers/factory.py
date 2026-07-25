from __future__ import annotations

from app.config import Settings
from app.infrastructure.providers.bothub_provider import BothubProvider
from app.infrastructure.providers.mock_provider import MockProvider
from app.services.llm_provider import LLMProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider_mode == "mock":
        return MockProvider()
    if settings.llm_provider_mode == "bothub":
        return BothubProvider(settings)
    raise NotImplementedError(
        f"LLM provider mode '{settings.llm_provider_mode}' is not wired up yet; "
        "use ARVEXO_LLM_PROVIDER_MODE=mock during development."
    )
