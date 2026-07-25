# Arvexo Radar: roadmap

**Версия:** v0.1.0 — Hackathon MVP
**Статус:** продуктовый план без календарных обещаний

## 1. Принцип планирования

Этапы определяются критериями выхода, а не неподтверждёнными датами. Следующий этап начинается после проверки предыдущего. Надёжный demo flow важнее числа функций.

## 2. Этап 0 — Dataset и технические spike

**Цель:** снять риски, связанные со средним запросом 100k токенов и качеством группировки.

**Работы:**

- получить/проверить reference dataset и canonical mapping;
- измерить длины, языки, timestamps, teams/directions и sensitive patterns;
- сравнить кандидатов local embeddings/classification/clustering на sample;
- проверить memory/time chunking pipeline без H100;
- подтвердить BotHub structured JSON contract и local/mock adapters;
- утвердить thresholds/configuration через ADR.

**Exit criteria:** dataset profile задокументирован; выбран воспроизводимый baseline; file/chunk/resource limits измерены; отсутствующие поля явно влияют на scope.

## 3. Этап 1 — Secure ingest foundation

**Цель:** безопасно загрузить dataset и получить проверяемую processing version.

**Scope:** Docker skeleton, DB migrations, upload, validation, mapping, normalization, masking, masked preview, jobs, status API, tests критической логики.

**Exit criteria:** malicious/invalid inputs обрабатываются безопасно; counts сходятся; raw text не появляется в logs/UI; mock demo запускается локально.

## 4. Этап 2 — Local analytics core

**Цель:** получить результаты без внешней LLM.

**Scope:** chunking, embeddings/cache, multi-label classification, `Other/Unknown`, clustering/noise, quality metrics, representative samples, prompt health, provenance.

**Exit criteria:** похожие/разные запросы проверены экспертной sample; длинные записи не truncated; repeated run сохраняет конфигурацию и даёт объяснимый результат.

## 5. Этап 3 — Generative layer

**Цель:** сформулировать названия, summaries, insights и recommendations из evidence.

**Scope:** provider abstraction, BotHub Gemini Flash, mock/local adapters, schemas, batching/cache/retry, graceful degradation.

**Exit criteria:** secret canaries не пересекают provider boundary; invalid JSON безопасно деградирует; каждое утверждение связано с evidence.

## 6. Этап 4 — Executive product experience

**Цель:** завершить основной сценарий CTO и AI Platform Owner.

**Scope:** upload/progress UI, Executive Overview, categories, use cases, explainability, prompt health/security, insights/recommendations, PDF report.

**Exit criteria:** [Demo Script](./19-demo-script.md) проходит end-to-end; dashboard/PDF согласованы; unavailable/partial/degraded состояния понятны.

## 7. Этап 5 — Hardening и submission

**Цель:** воспроизводимая сдача по критериям КРОК.

**Scope:** integration/e2e/security tests, performance measurement на reference hardware, clean setup verification, documentation review, backup demo assets, final report.

**Exit criteria:** репозиторий запускается по инструкции; нет critical findings; известные ограничения перечислены; demo не зависит от внешнего API благодаря mock/cache path.

## 8. После Hackathon MVP

Возможные направления, не входящие автоматически в scope:

- production authentication/SSO и детальный RBAC;
- управляемый taxonomy/feedback/annotation workflow;
- scheduled ingest и корпоративные connectors;
- outcome metrics для доказательной эффективности/ROI;
- production object storage, observability, backup/DR;
- multi-tenant administration;
- streaming/incremental clustering;
- расширенные export formats.

Каждое направление требует отдельного discovery, security review и изменения требований.

## 9. Зависимости и blockers

| Зависимость | Влияние | Решение |
|---|---|---|
| Реальный dataset | Models, limits, trends | Dataset audit до выбора алгоритмов |
| 100k-token average | Memory/time/context | Chunking spike и resource benchmark |
| Outcome data | Доказательство эффективности | Показывать proxy signals до появления данных |
| BotHub contract/key | Generated content | Mock mode и graceful degradation |
| Auth/retention owner | Production readiness | Не заявлять production readiness до решения |

## 10. Scope control

Feature принимается в текущий этап, только если прослеживается до P0 requirement, не ослабляет security/explainability и имеет acceptance criteria. «Вау-фича» не вытесняет must-have flow.

## 11. Связанные документы

- [Goals](./05-product-goals.md)
- [Non-goals](./06-non-goals.md)
- [Functional Requirements](./07-functional-requirements.md)
- [Architecture Decisions](./21-architecture-decisions.md)

