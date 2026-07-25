from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings


class ProxyConfigurationError(RuntimeError):
    pass


class OpenAIProxyClient:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.llm_proxy_timeout_seconds)
        )

    def _chat_completions_url(self) -> str:
        base_url = self._settings.llm_proxy_base_url
        if not base_url:
            raise ProxyConfigurationError("ARVEXO_LLM_PROXY_BASE_URL is not configured")
        normalized = base_url.rstrip("/")
        if normalized.endswith("/chat/completions"):
            return normalized
        return f"{normalized}/chat/completions"

    async def send(
        self,
        payload: dict[str, Any],
        *,
        inbound_authorization: str | None,
        stream: bool,
    ) -> httpx.Response:
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
        }
        api_key = self._settings.llm_proxy_api_key
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        elif inbound_authorization:
            headers["Authorization"] = inbound_authorization
        request = self._client.build_request(
            "POST", self._chat_completions_url(), headers=headers, json=payload
        )
        return await self._client.send(request, stream=stream)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
