from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    provider_mode: str = "mock"
    taxonomy_version: str = "taxonomy-v1"
    locale: str = "ru-RU"


class Degradation(BaseModel):
    code: str
    affected: list[str]
    details: dict = Field(default_factory=dict)


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


class DataQualityField(BaseModel):
    field: str
    present: int
    missing: int
    completeness: float


class DataQualityBlock(BaseModel):
    accepted: int
    accepted_with_warnings: int
    rejected: int
    total_rows: int
    warning_counts: dict[str, int]
    fields: list[DataQualityField]


class DistributionPoint(BaseModel):
    key: str
    label: str
    count: int
    share: float


class ActivityBlock(BaseModel):
    valid_timestamp_records: int
    missing_timestamp_records: int
    by_date: list[DistributionPoint]
    by_hour: list[DistributionPoint]


class SegmentPoint(BaseModel):
    value: str
    count: int
    share: float
    is_missing: bool = False


class RiskBreakdown(BaseModel):
    key: str
    count: int


class RiskSummary(BaseModel):
    total_findings: int
    affected_records: int
    affected_share: float
    by_severity: list[RiskBreakdown]
    by_type: list[RiskBreakdown]


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
    data_quality: DataQualityBlock
    activity: ActivityBlock
    segments: dict[str, list[SegmentPoint]]
    risk_summary: RiskSummary
    degradations: list[Degradation]
    limitations: list[str]
