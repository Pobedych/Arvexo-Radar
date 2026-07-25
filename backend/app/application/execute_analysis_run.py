"""ExecuteAnalysisStage / the run pipeline itself.

Runs the documented stage sequence — embedding, classifying, clustering,
generating, insights, completed (docs/09-architecture.md section 7) — inside
one worker job claim. Local stages (embedding/classifying/clustering) never
fail the whole run; only the two LLM-backed stages (naming, recommendations)
can degrade it, and even then local results are kept (AI-AC-05).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.domain.classification import classify_text
from app.domain.clustering import cluster_records
from app.domain.embeddings import EMBEDDING_MODEL_VERSION, cosine_similarity, embed_text
from app.domain.enums import RunStage, RunStatus
from app.domain.insights import (
    build_category_insights,
    build_prompt_health_insight,
    build_scenario_insights,
    trend_availability,
)
from app.domain.prompt_health import RecordForHealthCheck, evaluate_findings
from app.domain.representative_samples import select_representative_samples
from app.domain.taxonomy import CATEGORY_BY_ID
from app.infrastructure.db.models import (
    Classification,
    Finding,
    Insight,
    Recommendation,
    Scenario,
    ScenarioMember,
)
from app.repositories.analysis_repository import AnalysisRepository
from app.services.llm_provider import LLMOperation, LLMProvider, LLMProviderError

CLASSIFICATION_METHOD_VERSION = "keyword-fallback-v1"


class ExecuteAnalysisRun:
    def __init__(self, repository: AnalysisRepository, llm_provider: LLMProvider) -> None:
        self._repo = repository
        self._llm = llm_provider

    async def execute(self, run_id: uuid.UUID) -> None:
        run = await self._repo.get_run_by_id(run_id)
        if run is None:
            return

        run.status = RunStatus.RUNNING
        run.started_at = datetime.now(UTC)
        await self._repo.commit()
        degradations: list[dict] = []

        records = await self._repo.get_analyzable_records(run.dataset_version_id)
        records = [r for r in records if r.masked_text]

        if not records:
            run.status = RunStatus.FAILED
            run.error_code = "NO_ANALYZABLE_RECORDS"
            run.stage = RunStage.EMBEDDING
            run.completed_at = datetime.now(UTC)
            return

        # -- embedding (local) -------------------------------------------------
        run.stage = RunStage.EMBEDDING
        vectors: dict[str, list[float]] = {
            str(r.id): embed_text(r.masked_text) for r in records
        }

        # -- classifying (local) ------------------------------------------------
        run.stage = RunStage.CLASSIFYING
        category_counts: dict[str, int] = {}
        classifications: list[Classification] = []
        for record in records:
            for result in classify_text(record.masked_text):
                classifications.append(
                    Classification(
                        id=uuid.uuid4(),
                        run_id=run.id,
                        record_id=record.id,
                        category_id=result.category_id,
                        confidence=result.confidence,
                        reason=result.reason,
                        evidence_refs=[str(record.id)],
                        method_version=CLASSIFICATION_METHOD_VERSION,
                    )
                )
                category_counts[result.category_id] = category_counts.get(result.category_id, 0) + 1
        await self._repo.bulk_create_classifications(classifications)

        # -- clustering (local) --------------------------------------------------
        run.stage = RunStage.CLUSTERING
        clusters = cluster_records(vectors)
        total_records = len(records)

        scenario_rows: list[Scenario] = []
        scenario_members_by_scenario: dict[uuid.UUID, list[ScenarioMember]] = {}
        scenario_samples: dict[uuid.UUID, list[str]] = {}

        for cluster in clusters:
            scenario_id = uuid.uuid4()
            share = len(cluster.member_ids) / total_records
            scenario = Scenario(
                id=scenario_id,
                run_id=run.id,
                cluster_label=cluster.label,
                is_noise=cluster.is_noise,
                size=len(cluster.member_ids),
                share=share,
                quality={"cohesion": round(cluster.cohesion(vectors), 3)},
                category_ids=[],
                provenance={
                    "clustering_version": "greedy-cosine-v1",
                    "embedding_model_version": EMBEDDING_MODEL_VERSION,
                },
                generation_status="noise" if cluster.is_noise else "pending",
            )
            scenario_rows.append(scenario)

            members = []
            for record_id in cluster.member_ids:
                members.append(
                    ScenarioMember(
                        id=uuid.uuid4(),
                        scenario_id=scenario_id,
                        record_id=uuid.UUID(record_id),
                        similarity=round(cosine_similarity(vectors[record_id], cluster.centroid), 3),
                        is_representative=False,
                    )
                )
            scenario_members_by_scenario[scenario_id] = members

            if not cluster.is_noise:
                samples = select_representative_samples(
                    cluster.member_ids, vectors, cluster.centroid, limit=5
                )
                sample_ids = {s.record_id for s in samples}
                for member in members:
                    if str(member.record_id) in sample_ids:
                        member.is_representative = True
                        member.selection_reason = "closest_to_centroid_diverse"
                record_by_id = {str(r.id): r for r in records}
                scenario_samples[scenario_id] = [
                    record_by_id[s.record_id].masked_text for s in samples
                ]

        await self._repo.bulk_create_scenarios(scenario_rows)
        all_members = [m for members in scenario_members_by_scenario.values() for m in members]
        await self._repo.bulk_create_scenario_members(all_members)

        # -- generating (LLM: scenario naming) ------------------------------
        run.stage = RunStage.GENERATING
        for scenario in scenario_rows:
            if scenario.is_noise:
                continue
            samples = scenario_samples.get(scenario.id, [])
            try:
                result = await self._llm.generate(
                    operation=LLMOperation.SCENARIO_NAMING,
                    schema_version="v1",
                    evidence={
                        "cluster_id": scenario.cluster_label,
                        "typical_phrasings": samples,
                        "evidence_refs": [str(scenario.id)],
                    },
                    locale=run.config_snapshot.get("locale", "ru-RU"),
                    idempotency_key=f"{run.id}:scenario:{scenario.id}",
                )
                scenario.name = result.data.get("name")
                scenario.description = result.data.get("description")
                scenario.typical_phrasings = result.data.get("typical_phrasings", [])
                scenario.caveats = result.data.get("caveats", [])
                scenario.generation_status = "generated"
                run.model_provenance = {
                    "provider": result.provenance.provider,
                    "model": result.provenance.model,
                    "prompt_version": result.provenance.prompt_version,
                }
            except LLMProviderError:
                scenario.name = f"Кластер {scenario.cluster_label}"
                scenario.description = None
                scenario.generation_status = "degraded"
                degradations.append(
                    {"code": "LLM_PROVIDER_UNAVAILABLE", "affected": [f"scenario:{scenario.id}"]}
                )

        # -- insights (local rules) --------------------------------------------
        run.stage = RunStage.INSIGHTS
        health_records = [
            RecordForHealthCheck(
                record_id=str(r.id),
                masked_text=r.masked_text,
                token_count=r.token_count or 0,
                warnings=tuple(w for w in r.warnings if not w.startswith("V")),
            )
            for r in records
        ]
        finding_drafts = evaluate_findings(health_records)
        finding_rows = [
            Finding(
                id=uuid.uuid4(),
                run_id=run.id,
                record_id=uuid.UUID(f.record_id) if f.record_id else None,
                rule_id=f.rule_id,
                type=f.type,
                severity=f.severity,
                masked_evidence=f.masked_evidence,
                finding_metadata=f.metadata,
            )
            for f in finding_drafts
        ]
        await self._repo.bulk_create_findings(finding_rows)

        category_names = {cid: c.name for cid, c in CATEGORY_BY_ID.items()}
        insight_drafts = build_category_insights(category_counts, total_records, category_names)
        insight_drafts += build_scenario_insights(
            [
                (str(s.id), s.name or f"Кластер {s.cluster_label}", s.size, s.share)
                for s in scenario_rows
                if not s.is_noise
            ],
            total_records,
        )
        finding_counts: dict[str, int] = {}
        for f in finding_drafts:
            finding_counts[f.rule_id] = finding_counts.get(f.rule_id, 0) + 1
        ph_insight = build_prompt_health_insight(finding_counts, total_records)
        if ph_insight:
            insight_drafts.append(ph_insight)

        insight_rows = [
            Insight(
                id=uuid.uuid4(),
                run_id=run.id,
                type=d.type,
                statement=d.statement,
                evidence_refs=d.evidence_refs,
                confidence=d.confidence,
                limitations=d.limitations,
            )
            for d in insight_drafts
        ]
        await self._repo.bulk_create_insights(insight_rows)

        recommendation_rows: list[Recommendation] = []
        for insight_row, draft in zip(insight_rows[:3], insight_drafts[:3], strict=False):
            try:
                result = await self._llm.generate(
                    operation=LLMOperation.RECOMMENDATION,
                    schema_version="v1",
                    evidence={"linked_insight_ids": [str(insight_row.id)]},
                    locale=run.config_snapshot.get("locale", "ru-RU"),
                    idempotency_key=f"{run.id}:recommendation:{insight_row.id}",
                )
                recommendation_rows.append(
                    Recommendation(
                        id=uuid.uuid4(),
                        run_id=run.id,
                        insight_id=insight_row.id,
                        action=result.data.get("action", ""),
                        rationale=result.data.get("rationale", ""),
                        priority_basis=result.data.get("priority_basis", "usage_share"),
                        caveats=result.data.get("caveats", []),
                    )
                )
            except LLMProviderError:
                degradations.append(
                    {"code": "LLM_PROVIDER_UNAVAILABLE", "affected": [f"recommendation:{insight_row.id}"]}
                )
        await self._repo.bulk_create_recommendations(recommendation_rows)

        trend_available, trend_reason = trend_availability(
            total_records, sum(1 for r in records if r.timestamp is not None)
        )
        run.config_snapshot = {
            **run.config_snapshot,
            "trend_available": trend_available,
            "trend_unavailable_reason": trend_reason,
        }

        # -- completion -----------------------------------------------------
        run.degradations = degradations
        run.stage = RunStage.COMPLETED
        run.status = RunStatus.DEGRADED if degradations else RunStatus.COMPLETED
        run.completed_at = datetime.now(UTC)
