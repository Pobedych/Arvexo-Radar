"""Read-side queries for a completed/degraded run (docs/12-backend.md
`GetExecutiveOverview`, `GetCategory/ScenarioDetail`).

Kept out of the routers so routers stay free of aggregation logic
(docs/12-backend.md AC "routers не содержат domain calculations").
"""

from __future__ import annotations

import json
import uuid
from collections import Counter

from app.domain.errors import RunStateError
from app.domain.taxonomy import CATEGORY_BY_ID
from app.infrastructure.db.models import AnalysisRun
from app.repositories.analysis_repository import AnalysisRepository

MAX_SAMPLES = 5
MAX_FINDING_EXAMPLES = 3
SEGMENT_FIELDS = ("team", "direction", "agent_id", "language")


def _model_from_record_text(masked_text: str | None) -> str | None:
    if not masked_text:
        return None
    try:
        payload = json.loads(masked_text)
    except (json.JSONDecodeError, TypeError):
        return None
    model = payload.get("model") if isinstance(payload, dict) else None
    return str(model).strip() if model else None


def _distribution(counter: Counter[str], total: int) -> list[dict]:
    denominator = total or 1
    return [
        {"key": key, "label": key, "count": count, "share": count / denominator}
        for key, count in sorted(counter.items())
    ]


def _segment_distribution(counter: Counter[str], total: int) -> list[dict]:
    denominator = total or 1
    return [
        {
            "value": value,
            "count": count,
            "share": count / denominator,
            "is_missing": value == "__missing__",
        }
        for value, count in sorted(
            counter.items(), key=lambda item: (item[0] == "__missing__", -item[1], item[0])
        )
    ]


class RunQueries:
    def __init__(self, repository: AnalysisRepository) -> None:
        self._repo = repository

    async def _require_terminal(self, run: AnalysisRun) -> None:
        if run.status in ("queued", "running"):
            raise RunStateError(
                "Run has not produced results yet.", details={"status": run.status}
            )

    async def category_summaries(self, run_id: uuid.UUID) -> list[dict]:
        classifications = await self._repo.get_classifications(run_id)
        total = len({c.record_id for c in classifications}) or 1

        by_category: dict[str, list] = {}
        for c in classifications:
            by_category.setdefault(c.category_id, []).append(c)

        summaries = []
        for category_id, items in by_category.items():
            name = CATEGORY_BY_ID.get(category_id)
            summaries.append(
                {
                    "category_id": category_id,
                    "name": name.name if name else category_id,
                    "count": len(items),
                    "share": len(items) / total,
                    "avg_confidence": sum(i.confidence for i in items) / len(items),
                }
            )
        return sorted(summaries, key=lambda s: s["count"], reverse=True)

    async def category_detail(self, run: AnalysisRun, category_id: str) -> dict:
        await self._require_terminal(run)
        classifications = await self._repo.get_classifications(run.id)
        matching = [c for c in classifications if c.category_id == category_id]
        if not matching:
            known = CATEGORY_BY_ID.get(category_id)
            return {
                "category_id": category_id,
                "name": known.name if known else category_id,
                "count": 0,
                "share": 0.0,
                "avg_confidence": 0.0,
                "samples": [],
            }

        total = len({c.record_id for c in classifications}) or 1
        records = await self._repo.get_records_by_ids([c.record_id for c in matching])

        samples = [
            {
                "record_id": c.record_id,
                "masked_text": records[c.record_id].masked_text,
                "confidence": c.confidence,
                "reason": c.reason,
            }
            for c in sorted(matching, key=lambda c: c.confidence, reverse=True)[:MAX_SAMPLES]
            if c.record_id in records
        ]
        name = CATEGORY_BY_ID.get(category_id)
        return {
            "category_id": category_id,
            "name": name.name if name else category_id,
            "count": len(matching),
            "share": len(matching) / total,
            "avg_confidence": sum(c.confidence for c in matching) / len(matching),
            "samples": samples,
        }

    async def scenario_summaries(self, run_id: uuid.UUID) -> list[dict]:
        scenarios = await self._repo.get_scenarios(run_id)
        return [
            {
                "scenario_id": s.id,
                "name": s.name,
                "description": s.description,
                "size": s.size,
                "share": s.share,
                "quality": s.quality,
                "category_ids": s.category_ids,
                "generation_status": s.generation_status,
                "is_noise": s.is_noise,
            }
            for s in scenarios
        ]

    async def scenario_detail(self, run: AnalysisRun, scenario_id: uuid.UUID) -> dict | None:
        await self._require_terminal(run)
        scenario = await self._repo.get_scenario(run_id=run.id, scenario_id=scenario_id)
        if scenario is None:
            return None

        members = await self._repo.get_scenario_members(scenario_id)
        representative = [m for m in members if m.is_representative]
        records = await self._repo.get_records_by_ids([m.record_id for m in representative])

        samples = [
            {
                "record_id": m.record_id,
                "masked_text": records[m.record_id].masked_text,
                "similarity_to_centroid": m.similarity,
                "selection_reason": m.selection_reason,
            }
            for m in representative
            if m.record_id in records
        ]

        return {
            "scenario_id": scenario.id,
            "name": scenario.name,
            "description": scenario.description,
            "typical_phrasings": scenario.typical_phrasings,
            "size": scenario.size,
            "share": scenario.share,
            "quality": scenario.quality,
            "category_ids": scenario.category_ids,
            "generation_status": scenario.generation_status,
            "caveats": scenario.caveats,
            "evidence_count": len(members),
            "samples": samples,
        }

    async def insights_and_recommendations(self, run_id: uuid.UUID) -> tuple[list[dict], list[dict]]:
        insights = await self._repo.get_insights(run_id)
        recommendations = await self._repo.get_recommendations(run_id)
        insight_payload = [
            {
                "insight_id": i.id,
                "type": i.type,
                "statement": i.statement,
                "evidence_refs": i.evidence_refs,
                "confidence": i.confidence,
                "limitations": i.limitations,
            }
            for i in insights
        ]
        recommendation_payload = [
            {
                "recommendation_id": r.id,
                "action": r.action,
                "rationale": r.rationale,
                "linked_insight_id": r.insight_id,
                "priority_basis": r.priority_basis,
                "caveats": r.caveats,
            }
            for r in recommendations
        ]
        return insight_payload, recommendation_payload

    async def overview(self, run: AnalysisRun, *, dataset_id: uuid.UUID, total_records: int) -> dict:
        await self._require_terminal(run)

        categories = await self.category_summaries(run.id)
        scenarios = [s for s in await self.scenario_summaries(run.id) if not s["is_noise"]]
        findings = await self.finding_summaries(run.id)
        insights, recommendations = await self.insights_and_recommendations(run.id)
        dashboard_metrics = await self.dashboard_metrics(run, total_records=total_records)

        trend_available = bool(run.config_snapshot.get("trend_available"))
        trend_reason = run.config_snapshot.get("trend_unavailable_reason")

        limitations = ["classification_uses_keyword_fallback", "clustering_uses_placeholder_embeddings"]
        if run.status == "degraded":
            limitations.append("run_degraded_llm_wording_partial")

        return {
            "run_id": run.id,
            "dataset_id": dataset_id,
            "status": run.status,
            "total_records": total_records,
            "denominator": total_records,
            "top_categories": categories[:5],
            "top_scenarios": sorted(scenarios, key=lambda s: s["size"], reverse=True)[:5],
            "top_findings": findings[:5],
            "insights": insights,
            "recommendations": recommendations,
            "trend": {"available": trend_available, "reason": trend_reason},
            **dashboard_metrics,
            "degradations": run.degradations,
            "limitations": limitations,
        }

    async def dashboard_metrics(self, run: AnalysisRun, *, total_records: int) -> dict:
        version = await self._repo.get_dataset_version(run.dataset_version_id)
        records = await self._repo.get_analyzable_records(run.dataset_version_id)
        findings = await self._repo.get_findings(run.id)

        validation = version.validation_summary if version is not None else {}
        accepted = int(validation.get("accepted", 0))
        accepted_with_warnings = int(validation.get("accepted_with_warnings", 0))
        rejected = int(validation.get("rejected", 0))

        warning_counts: Counter[str] = Counter()
        date_counts: Counter[str] = Counter()
        hour_counts: Counter[str] = Counter()
        segment_counts = {field: Counter() for field in (*SEGMENT_FIELDS, "model")}
        present_counts: Counter[str] = Counter()

        for record in records:
            warning_counts.update(record.warnings or [])

            if record.timestamp is not None:
                date_counts[record.timestamp.date().isoformat()] += 1
                bucket_start = (record.timestamp.hour // 3) * 3
                bucket_key = f"{bucket_start:02d}:00"
                hour_counts[bucket_key] += 1

            metadata = record.metadata_json or {}
            for field in SEGMENT_FIELDS:
                value = str(metadata.get(field) or "").strip()
                segment_counts[field][value or "__missing__"] += 1
                if value:
                    present_counts[field] += 1

            model = str(metadata.get("model") or "").strip() or _model_from_record_text(
                record.masked_text
            )
            segment_counts["model"][model or "__missing__"] += 1
            if model:
                present_counts["model"] += 1

        for field in (*SEGMENT_FIELDS, "model"):
            missing = max(total_records - sum(segment_counts[field].values()), 0)
            if missing:
                segment_counts[field]["__missing__"] += missing

        severity_counts = Counter(f.severity for f in findings)
        type_counts = Counter(f.type for f in findings)
        affected_record_ids = {f.record_id for f in findings if f.record_id is not None}
        valid_timestamps = sum(date_counts.values())

        quality_fields = []
        for field in (*SEGMENT_FIELDS, "model"):
            present = present_counts[field]
            missing = max(total_records - present, 0)
            quality_fields.append(
                {
                    "field": field,
                    "present": present,
                    "missing": missing,
                    "completeness": present / (total_records or 1),
                }
            )

        return {
            "data_quality": {
                "accepted": accepted,
                "accepted_with_warnings": accepted_with_warnings,
                "rejected": rejected,
                "total_rows": accepted + accepted_with_warnings + rejected,
                "warning_counts": dict(sorted(warning_counts.items())),
                "fields": quality_fields,
            },
            "activity": {
                "valid_timestamp_records": valid_timestamps,
                "missing_timestamp_records": max(total_records - valid_timestamps, 0),
                "by_date": _distribution(date_counts, valid_timestamps),
                "by_hour": _distribution(hour_counts, valid_timestamps),
            },
            "segments": {
                field: _segment_distribution(counter, total_records)
                for field, counter in segment_counts.items()
            },
            "risk_summary": {
                "total_findings": len(findings),
                "affected_records": len(affected_record_ids),
                "affected_share": len(affected_record_ids) / (total_records or 1),
                "by_severity": [
                    {"key": key, "count": count}
                    for key, count in sorted(severity_counts.items())
                ],
                "by_type": [
                    {"key": key, "count": count} for key, count in sorted(type_counts.items())
                ],
            },
        }

    async def finding_summaries(self, run_id: uuid.UUID, *, finding_type: str | None = None) -> list[dict]:
        findings = await self._repo.get_findings(run_id, finding_type=finding_type)
        by_rule: dict[str, list] = {}
        for f in findings:
            by_rule.setdefault(f.rule_id, []).append(f)

        summaries = []
        for rule_id, items in by_rule.items():
            summaries.append(
                {
                    "rule_id": rule_id,
                    "type": items[0].type,
                    "severity": items[0].severity,
                    "count": len(items),
                    "examples": [
                        i.masked_evidence for i in items[:MAX_FINDING_EXAMPLES] if i.masked_evidence
                    ],
                }
            )
        return sorted(summaries, key=lambda s: s["count"], reverse=True)
