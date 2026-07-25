"""Deterministic mock LLM provider.

No network calls, no API key required (docs/12-backend.md AC "mock mode
works without external credentials"). Output shape matches the schemas in
docs/10-ai-pipeline.md section 10, built only from the given `evidence` so no
invented facts are introduced.
"""

from __future__ import annotations

from typing import Any

from app.services.llm_provider import LLMOperation, LLMProvenance, LLMResult

_PROMPT_VERSION = "mock-v1"


class MockProvider:
    async def generate(
        self,
        *,
        operation: LLMOperation,
        schema_version: str,
        evidence: dict[str, Any],
        locale: str,
        idempotency_key: str,
    ) -> LLMResult:
        provenance = LLMProvenance(
            provider="mock",
            model="mock-deterministic",
            prompt_version=_PROMPT_VERSION,
            schema_version=schema_version,
        )

        if operation is LLMOperation.SCENARIO_NAMING:
            data = self._scenario_naming(evidence)
        elif operation is LLMOperation.INSIGHT_WORDING:
            data = self._insight_wording(evidence)
        elif operation is LLMOperation.RECOMMENDATION:
            data = self._recommendation(evidence)
        else:  # pragma: no cover - exhaustive by enum
            raise ValueError(f"Unsupported operation: {operation}")

        return LLMResult(data=data, provenance=provenance, degraded=False)

    @staticmethod
    def _scenario_naming(evidence: dict[str, Any]) -> dict[str, Any]:
        phrasings = evidence.get("typical_phrasings", [])
        seed = phrasings[0] if phrasings else evidence.get("cluster_id", "scenario")
        return {
            "name": f"Cluster {seed}"[:80],
            "description": "Сгенерировано mock-провайдером на основе representative samples.",
            "typical_phrasings": phrasings[:3],
            "evidence_refs": evidence.get("evidence_refs", []),
            "caveats": ["mock_provider_output"],
        }

    @staticmethod
    def _insight_wording(evidence: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": evidence.get("type", "observation"),
            "statement": f"Наблюдение на основе {len(evidence.get('evidence_refs', []))} записей.",
            "evidence_refs": evidence.get("evidence_refs", []),
            "confidence": evidence.get("confidence", 0.0),
            "limitations": ["mock_provider_output"],
        }

    @staticmethod
    def _recommendation(evidence: dict[str, Any]) -> dict[str, Any]:
        return {
            "action": "Проверить сценарий с владельцем процесса.",
            "rationale": "Сформировано mock-провайдером из переданных insight.",
            "linked_insight_ids": evidence.get("linked_insight_ids", []),
            "priority_basis": "usage_share",
            "caveats": ["mock_provider_output"],
        }
