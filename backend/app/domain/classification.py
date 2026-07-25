"""Multi-label keyword classification (docs/10-ai-pipeline.md section 6).

Explicitly the "explainable fallback" the docs allow, not a semantic
classifier: a real model requires the same reference-dataset benchmark
deferred throughout this pipeline. `Other/Unknown` is assigned whenever
nothing clears the threshold, per the documented threshold policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.taxonomy import CATEGORIES, OTHER_UNKNOWN, TAXONOMY_VERSION

LABEL_THRESHOLD = 0.12
METHOD_VERSION = f"keyword-fallback-v1+{TAXONOMY_VERSION}"


@dataclass(frozen=True)
class ClassificationResult:
    category_id: str
    confidence: float
    reason: str
    matched_keywords: tuple[str, ...]


def classify_text(masked_text: str) -> list[ClassificationResult]:
    text = masked_text.lower()
    results: list[ClassificationResult] = []

    for category in CATEGORIES:
        if category.id == OTHER_UNKNOWN or not category.keywords:
            continue
        matched = tuple(kw for kw in category.keywords if kw in text)
        if not matched:
            continue
        confidence = min(1.0, len(matched) / max(2, len(category.keywords)) + 0.2)
        if confidence < LABEL_THRESHOLD:
            continue
        results.append(
            ClassificationResult(
                category_id=category.id,
                confidence=round(confidence, 3),
                reason=f"Совпадение по ключевым словам: {', '.join(matched)}.",
                matched_keywords=matched,
            )
        )

    if not results:
        return [
            ClassificationResult(
                category_id=OTHER_UNKNOWN,
                confidence=1.0,
                reason="Ни одна категория не набрала порог уверенности по ключевым словам.",
                matched_keywords=(),
            )
        ]

    return sorted(results, key=lambda r: r.confidence, reverse=True)
