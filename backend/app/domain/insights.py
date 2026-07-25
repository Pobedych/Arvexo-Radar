"""Local insight computation (docs/10-ai-pipeline.md section 13,
docs/08-dataset.md section 9).

Every statement here is a plain, locally-derived observation: counts,
shares, and repetition, never an outcome/ROI claim (`AI-AC-04`, ROI is
explicitly out of scope). Insight *wording* may later be smoothed by an LLM
call, but the evidence list and confidence are fixed before that call, so
the model cannot introduce unsupported facts.
"""

from __future__ import annotations

from dataclasses import dataclass

MIN_SHARE_FOR_OBSERVATION = 0.05


@dataclass(frozen=True)
class InsightDraft:
    type: str  # observation | hypothesis
    statement: str
    evidence_refs: list[str]
    confidence: float
    limitations: list[str]


def build_category_insights(
    category_counts: dict[str, int],
    total_records: int,
    category_names: dict[str, str],
) -> list[InsightDraft]:
    if total_records == 0:
        return []

    drafts: list[InsightDraft] = []
    ranked = sorted(category_counts.items(), key=lambda kv: kv[1], reverse=True)
    for category_id, count in ranked[:3]:
        share = count / total_records
        if share < MIN_SHARE_FOR_OBSERVATION:
            continue
        name = category_names.get(category_id, category_id)
        drafts.append(
            InsightDraft(
                type="observation",
                statement=f"Категория «{name}» встречается в {share:.0%} обработанных запросов "
                f"({count} из {total_records}).",
                evidence_refs=[f"category:{category_id}"],
                confidence=min(0.95, 0.5 + share),
                limitations=["multi_label_share_may_overlap"],
            )
        )
    return drafts


def build_scenario_insights(
    scenarios: list[tuple[str, str, int, float]],  # (scenario_id, name, size, share)
    total_records: int,
) -> list[InsightDraft]:
    drafts: list[InsightDraft] = []
    for scenario_id, name, size, share in scenarios[:3]:
        if size < 3:
            continue
        drafts.append(
            InsightDraft(
                type="observation",
                statement=f"Обнаружен устойчивый сценарий «{name}»: {size} запросов "
                f"({share:.0%} от датасета).",
                evidence_refs=[f"scenario:{scenario_id}"],
                confidence=min(0.9, 0.4 + share),
                limitations=["cluster_boundary_is_approximate"],
            )
        )
    return drafts


def build_prompt_health_insight(finding_counts: dict[str, int], total_records: int) -> InsightDraft | None:
    if total_records == 0 or not finding_counts:
        return None
    total_findings = sum(finding_counts.values())
    top_rule = max(finding_counts.items(), key=lambda kv: kv[1])
    share = total_findings / total_records
    return InsightDraft(
        type="observation",
        statement=f"На {total_findings} находок prompt health/security приходится "
        f"{share:.0%} от объёма записей; чаще всего срабатывает правило {top_rule[0]} "
        f"({top_rule[1]} раз).",
        evidence_refs=[f"finding_rule:{top_rule[0]}"],
        confidence=0.6,
        limitations=["finding_is_potential_not_confirmed"],
    )


def trend_availability(
    total_records: int, trend_eligible_records: int, *, min_share: float = 0.5, min_periods: int = 2
) -> tuple[bool, str | None]:
    if total_records == 0:
        return False, "no_records"
    share = trend_eligible_records / total_records
    if share < min_share:
        return False, "insufficient_timestamp_coverage"
    return True, None
