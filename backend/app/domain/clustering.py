"""Deterministic greedy clustering (docs/10-ai-pipeline.md section 7).

docs/09-architecture.md defers the final clustering algorithm to a
benchmark comparison fixed by ADR before "production behavior" is settled.
This is a documented, versioned placeholder that satisfies the section 7
contract (no pre-set cluster count, noise support, saved parameters/seed,
returned quality diagnostics) using only stdlib — no scikit-learn/hdbscan
install required for the MVP demo path.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.embeddings import cosine_similarity

CLUSTERING_VERSION = "greedy-cosine-v1"
SIMILARITY_THRESHOLD = 0.35
MIN_CLUSTER_SIZE = 3


@dataclass
class ClusterMember:
    record_id: str
    similarity_to_centroid: float


@dataclass
class Cluster:
    label: int
    member_ids: list[str] = field(default_factory=list)
    centroid: list[float] = field(default_factory=list)
    is_noise: bool = False

    def cohesion(self, vectors: dict[str, list[float]]) -> float:
        if not self.member_ids:
            return 0.0
        sims = [cosine_similarity(vectors[m], self.centroid) for m in self.member_ids]
        return sum(sims) / len(sims)


def _average_vectors(vectors: list[list[float]]) -> list[float]:
    dim = len(vectors[0])
    sums = [0.0] * dim
    for v in vectors:
        for i, x in enumerate(v):
            sums[i] += x
    n = len(vectors)
    return [s / n for s in sums]


def cluster_records(
    record_vectors: dict[str, list[float]],
    *,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
    min_cluster_size: int = MIN_CLUSTER_SIZE,
) -> list[Cluster]:
    """Greedy single-pass assignment in input-order: each record joins the
    first existing cluster whose centroid it is similar enough to, else
    starts a new one. Deterministic given a stable `record_vectors` order
    (a dict preserves insertion order in Python)."""

    clusters: list[Cluster] = []

    for record_id, vector in record_vectors.items():
        best_cluster = None
        best_similarity = similarity_threshold
        for cluster in clusters:
            similarity = cosine_similarity(vector, cluster.centroid)
            if similarity >= best_similarity:
                best_similarity = similarity
                best_cluster = cluster

        if best_cluster is None:
            new_cluster = Cluster(label=len(clusters), member_ids=[record_id], centroid=vector)
            clusters.append(new_cluster)
        else:
            best_cluster.member_ids.append(record_id)
            member_vectors = [record_vectors[m] for m in best_cluster.member_ids]
            best_cluster.centroid = _average_vectors(member_vectors)

    for cluster in clusters:
        if len(cluster.member_ids) < min_cluster_size:
            cluster.is_noise = True

    return clusters
