from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RadarMetadata(BaseModel):
    user_id: str | None = Field(default=None, max_length=1024)
    role: str | None = Field(default=None, max_length=150)
    department: str | None = Field(default=None, max_length=255)
    team: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    agent_id: str | None = Field(default=None, max_length=255)
    scenario_id: str | None = Field(default=None, max_length=255)
    scenario: str | None = Field(default=None, max_length=255)
    tool_calls: list[str] = Field(default_factory=list, max_length=50)


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str
    content: Any = None


class ChatCompletionRequest(BaseModel):
    """Minimal typed envelope that preserves unknown OpenAI-compatible fields."""

    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1, max_length=255)
    messages: list[ChatMessage]
    stream: bool = False
    stream_options: dict[str, Any] | None = None
    metadata: RadarMetadata | None = None

    def provider_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"metadata"}, exclude_none=True)
