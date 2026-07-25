"""Local embedding stand-in (docs/10-ai-pipeline.md section 5).

docs/10-ai-pipeline.md explicitly defers the real local embedding model to a
reference-dataset benchmark that has not happened. Shipping the pipeline
without any embedding step would block classification/clustering entirely,
so this module provides a deterministic, dependency-free feature-hashing
vectorizer as an explicit, versioned placeholder — never described to users
as a trained semantic model. Swapping in a real sentence embedding model
later only touches this module and bumps `EMBEDDING_MODEL_VERSION`, which
invalidates dependent vectors per docs/10-ai-pipeline.md section 5.
"""

from __future__ import annotations

import hashlib
import math
import re

EMBEDDING_MODEL_VERSION = "hashing-v1-384d"
EMBEDDING_DIM = 384

_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 1]


def embed_text(text: str) -> list[float]:
    """Hashed bag-of-words, L2-normalized. Deterministic across runs and
    processes: no random seed, no model weights to load."""

    vector = [0.0] * EMBEDDING_DIM
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))
