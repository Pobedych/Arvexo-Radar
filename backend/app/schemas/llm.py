"""Strict structured-output schemas shared by external LLM adapters."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _LLMOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ScenarioNamingOutput(_LLMOutput):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=1000)
    typical_phrasings: list[str] = Field(default_factory=list, max_length=5)
    evidence_refs: list[str] = Field(default_factory=list, max_length=100)
    caveats: list[str] = Field(default_factory=list, max_length=10)


class InsightWordingOutput(_LLMOutput):
    type: str = Field(min_length=1, max_length=80)
    statement: str = Field(min_length=1, max_length=1200)
    evidence_refs: list[str] = Field(default_factory=list, max_length=100)
    confidence: float = Field(ge=0, le=1)
    limitations: list[str] = Field(default_factory=list, max_length=10)


class RecommendationOutput(_LLMOutput):
    action: str = Field(min_length=1, max_length=600)
    rationale: str = Field(min_length=1, max_length=1200)
    linked_insight_ids: list[str] = Field(default_factory=list, max_length=20)
    priority_basis: str = Field(min_length=1, max_length=120)
    caveats: list[str] = Field(default_factory=list, max_length=10)
