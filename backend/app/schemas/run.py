from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class CreateRunRequest(BaseModel):
    provider_mode: str = "mock"
    taxonomy_version: str = "taxonomy-v1"
    locale: str = "ru-RU"


class Degradation(BaseModel):
    code: str
    affected: list[str]


class RunResponse(BaseModel):
    run_id: UUID
    dataset_id: UUID
    status: str
    stage: str | None
    degradations: list[Degradation]
    provenance: dict


class CategorySummary(BaseModel):
    category_id: str
    name: str
    count: int
    share: float
    avg_confidence: float


class ClassifiedSample(BaseModel):
    record_id: UUID
    masked_text: str
    confidence: float
    reason: str


class CategoryDetailResponse(BaseModel):
    category_id: str
    name: str
    count: int
    share: float
    avg_confidence: float
    samples: list[ClassifiedSample]


class ScenarioSummary(BaseModel):
    scenario_id: UUID
    name: str | None
    description: str | None
    size: int
    share: float
    quality: dict
    category_ids: list[str]
    generation_status: str
    is_noise: bool


class RepresentativeSample(BaseModel):
    record_id: UUID
    masked_text: str
    similarity_to_centroid: float
    selection_reason: str | None


class ScenarioDetailResponse(BaseModel):
    scenario_id: UUID
    name: str | None
    description: str | None
    typical_phrasings: list[str]
    size: int
    share: float
    quality: dict
    category_ids: list[str]
    generation_status: str
    caveats: list[str]
    evidence_count: int
    samples: list[RepresentativeSample]


class InsightResponse(BaseModel):
    insight_id: UUID
    type: str
    statement: str
    evidence_refs: list[str]
    confidence: float
    limitations: list[str]


class RecommendationResponse(BaseModel):
    recommendation_id: UUID
    action: str
    rationale: str
    linked_insight_id: UUID | None
    priority_basis: str
    caveats: list[str]


class InsightsResponse(BaseModel):
    insights: list[InsightResponse]
    recommendations: list[RecommendationResponse]


class FindingSummary(BaseModel):
    rule_id: str
    type: str
    severity: str
    count: int
    examples: list[str]


class FindingsResponse(BaseModel):
    findings: list[FindingSummary]


class TrendBlock(BaseModel):
    available: bool
    reason: str | None


class OverviewResponse(BaseModel):
    run_id: UUID
    dataset_id: UUID
    status: str
    total_records: int
    denominator: int
    top_categories: list[CategorySummary]
    top_scenarios: list[ScenarioSummary]
    top_findings: list[FindingSummary]
    insights: list[InsightResponse]
    recommendations: list[RecommendationResponse]
    trend: TrendBlock
    degradations: list[Degradation]
    limitations: list[str]
