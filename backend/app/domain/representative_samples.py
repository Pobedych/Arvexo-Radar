"""Representative sample selection (docs/10-ai-pipeline.md section 8).

Picks members closest to the cluster centroid, skipping near-duplicates so
the samples shown to a user (and sent to the LLM for naming) are diverse
rather than repeats of the same phrasing. Never a random "nice-looking"
pick, per the documented constraint.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.embeddings import cosine_similarity

NEAR_DUPLICATE_SIMILARITY = 0.97


@dataclass(frozen=True)
class RepresentativeSample:
    record_id: str
    similarity_to_centroid: float
    selection_reason: str


def select_representative_samples(
    member_ids: list[str],
    vectors: dict[str, list[float]],
    centroid: list[float],
    *,
    limit: int = 5,
) -> list[RepresentativeSample]:
    ranked = sorted(
        member_ids,
        key=lambda m: cosine_similarity(vectors[m], centroid),
        reverse=True,
    )

    selected: list[RepresentativeSample] = []
    for record_id in ranked:
        if len(selected) >= limit:
            break
        vector = vectors[record_id]
        is_near_duplicate = any(
            cosine_similarity(vector, vectors[s.record_id]) >= NEAR_DUPLICATE_SIMILARITY
            for s in selected
        )
        if is_near_duplicate:
            continue
        selected.append(
            RepresentativeSample(
                record_id=record_id,
                similarity_to_centroid=round(cosine_similarity(vector, centroid), 3),
                selection_reason="closest_to_centroid_diverse",
            )
        )

    return selected
