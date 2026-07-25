# Arvexo Radar: AI/ML pipeline

**Версия:** v0.1.0 — Hackathon MVP
**Статус:** спецификация AI/ML

## 1. Принципы

1. Deterministic/local processing предшествует генерации.
2. Raw sensitive data не пересекают external-provider boundary.
3. Каждая модель, taxonomy, prompt и threshold версионируются.
4. Низкая уверенность становится `Other/Unknown`, noise или caveat.
5. LLM формулирует текст только из переданного evidence.
6. H100 не используется; основной LLM — Gemini Flash через BotHub API.

## 2. Этапы

| Этап | Вход | Выход | Выполнение |
|---|---|---|---|
| Validation | CSV rows | accepted/rejected records | Local deterministic |
| Normalization | accepted text | normalized text | Local deterministic |
| Masking | normalized text | masked text + findings | Local deterministic |
| Chunking | masked text | ordered chunks | Local deterministic |
| Embeddings | chunks | chunk/record vectors | Local model |
| Classification | vectors/text features | multi-label categories | Local model/rules |
| Clustering | record vectors | clusters + noise | Local algorithm |
| Selection | clusters | representative evidence | Local deterministic |
| Naming/Summary | minimal evidence | structured scenario text | LLM provider |
| Insights | aggregates/evidence | typed insights | Local rules + bounded LLM wording |
| Recommendations | insights | structured actions | LLM provider with evidence |

## 3. Preprocessing и chunking

- Token counting использует tokenizer выбранной model version.
- Chunk boundaries стремятся сохранять абзацы/предложения, но имеют hard token cap.
- Overlap ограничен и версионирован.
- Пустые chunks отбрасываются с count.
- Record embedding агрегирует chunks по утверждённой стратегии; первые chunks не получают неявного преимущества.
- Для 100k-token среднего запроса pipeline работает потоково/batched и не держит весь dataset в GPU memory.

Конкретные `chunk_size`, `overlap` и aggregation method выбираются benchmark на reference dataset и фиксируются configuration snapshot до реализации production behavior.

## 4. Sensitive Data Masking

Детерминированные detectors покрывают email, phone и распространённые key/secret formats. Detection результат — потенциальный finding, а не гарантия утечки. После masking создаётся `sanitized_content_hash`; raw text не используется в cache keys и provider payload.

## 5. Embeddings

Требования к локальной embedding-модели:

- поддержка языков фактического dataset;
- локальное выполнение без H100;
- документированный context limit;
- стабильная model/version identifier;
- допустимая лицензия для продукта;
- измеренное время и качество на reference sample.

Конкретная модель не утверждается до dataset audit. Замена модели инвалидирует зависимые cache entries и требует нового run.

## 6. Classification

Multi-label classifier выдаёт список `{category_id, confidence, reason, evidence_refs}`. Taxonomy хранится отдельно и содержит `Other/Unknown`.

Threshold policy:

- значения выше label threshold назначаются;
- при отсутствии labels назначается `Other/Unknown`;
- borderline cases сохраняют caveat;
- thresholds выбираются на размеченной validation sample;
- отсутствие размеченной sample означает, что confidence нельзя называть calibrated probability.

Baseline keyword rules допустимы только как объяснимый fallback и не должны быть единственным методом семантической классификации.

## 7. Scenario Clustering

Алгоритм должен:

- не требовать заранее точного числа кластеров либо выбирать его воспроизводимо;
- поддерживать noise/outliers;
- сохранять parameters и random seed;
- возвращать cluster quality и global diagnostics;
- не создавать название до проверки minimum cluster support.

Кандидаты алгоритмов сравниваются на reference dataset; библиотека и финальный алгоритм фиксируются ADR перед кодом. Качество проверяется сочетанием внутренних metrics и экспертной оценки «похожие вместе, разные разделены».

## 8. Representative samples

Samples выбираются локально: близость к medoid/centroid, разнообразие и отсутствие дубликатов. Возвращается короткий masked excerpt, record reference и selection reason. Случайный «красивый» пример запрещён.

## 9. LLM provider contract

```text
generate(operation, schema_version, evidence, locale, idempotency_key)
  -> structured result + provider/model/prompt provenance
```

Реализации:

- `BothubGeminiProvider` — основной API mode;
- `MockProvider` — детерминированные fixtures без сети;
- `LocalProvider` — optional adapter для локального тестового endpoint/runtime; конкретный runtime не фиксируется.

Все provider responses проходят JSON schema/Pydantic validation. Chain-of-thought не запрашивается и не сохраняется.

## 10. Prompt и output schemas

Scenario output:

```json
{
  "name": "Подготовка сводок по почте",
  "description": "Запросы на краткое структурирование писем.",
  "typical_phrasings": ["Собери сводку писем за день"],
  "evidence_refs": ["record:masked-id"],
  "caveats": []
}
```

Insight output содержит `type`, `statement`, `evidence_refs`, `confidence`, `limitations`. Recommendation output содержит `action`, `rationale`, `linked_insight_ids`, `priority_basis`, `caveats`. Неизвестные поля запрещаются schema.

## 11. Batch, cache и retry

- Batch ограничен provider token/request limits и privacy budget.
- Cache key включает operation, provider, model, prompt version, schema version и sanitized evidence hash.
- Retry только для timeout, connection failure, `429` и selected `5xx`.
- Invalid JSON получает ограниченный repair retry без добавления raw data.
- Authentication/permission errors не повторяются.
- После исчерпания retry возвращается typed failure и fallback.

Числа попыток и timeout конфигурируются и тестируются; секреты не включаются в configuration snapshot.

## 12. Graceful degradation

| Отказ | Поведение |
|---|---|
| External API unavailable | Сохранить local analytics, использовать cache/mock-safe template, run=`degraded` |
| Invalid structured output | Retry, затем deterministic fallback без новых фактов |
| Embedding model unavailable | Run=`failed`; clustering/classification не подделываются |
| Clustering only noise | Показать отсутствие устойчивых сценариев |
| Low classification confidence | `Other/Unknown` |
| Missing timestamp | Trends unavailable |

## 13. Insights и эффективность

Local calculations определяют counts, shares, trends, repeated patterns и findings. LLM может формулировать readable statement, но evidence list создаётся до вызова. «Эффективность» без outcomes показывается как usage/proxy signal: распространённость, повторяемость, рост, prompt friction или automation potential. ROI не генерируется.

## 14. Evaluation

- Classification: экспертная размеченная sample, per-label precision/recall/F1 после её появления.
- Clustering: expert pair/group review плюс подходящие internal metrics.
- Naming: соответствие evidence, ясность, отсутствие unsupported claims.
- Stability: повторный run и perturbation checks.
- Performance: stage timings на согласованном hardware/reference dataset.
- Safety: secret canaries не должны появляться в provider payload/output/logs.

До baseline документация не задаёт фиктивные thresholds. Demo dataset не используется как единственное доказательство качества.

## 15. Критерии приёмки

- **AI-AC-01:** полный raw prompt не отправляется внешней LLM.
- **AI-AC-02:** output не принимается без schema validation.
- **AI-AC-03:** model/prompt/config provenance сохранён.
- **AI-AC-04:** low confidence не скрывается.
- **AI-AC-05:** provider outage сохраняет local results.
- **AI-AC-06:** 100k-token record не обрезается молча.

## 16. Связанные документы

- [Dataset](./08-dataset.md)
- [Architecture](./09-architecture.md)
- [Security](./16-security.md)
- [Architecture Decisions](./21-architecture-decisions.md)

