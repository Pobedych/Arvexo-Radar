# Arvexo Radar: архитектурные решения

**Версия:** v0.1.0 — Hackathon MVP
**Статус:** журнал ADR

## 1. Статусы

- **Accepted** — решение утверждено и обязательно.
- **Proposed** — решение требует проверки/утверждения до реализации.
- **Deferred** — не входит в текущий scope.
- **Superseded** — заменено более новым ADR.

## 2. Реестр

| ADR | Решение | Статус |
|---|---|---|
| ADR-001 | Зафиксированный web/backend/database/infrastructure stack | Accepted |
| ADR-002 | Local-first analytics и bounded external LLM | Accepted |
| ADR-003 | LLM provider abstraction: BotHub, mock, local test adapter | Accepted |
| ADR-004 | H100 не используется в v0.1.0 | Accepted |
| ADR-005 | 100k токенов — средний размер запроса | Accepted |
| ADR-006 | PostgreSQL jobs вместо дополнительного broker | Accepted |
| ADR-007 | CSV как единственный upload format MVP | Accepted |
| ADR-008 | Конкретная embedding model | Proposed |
| ADR-009 | Classification method/thresholds | Proposed |
| ADR-010 | Clustering algorithm/quality metric | Proposed |
| ADR-011 | Production IAM, retention и storage | Deferred |

## 3. ADR-001 — Технологический стек

**Контекст:** продукт требует web dashboard, Python AI/ML pipeline, vectors и локальный запуск.
**Решение:** Next.js 15, TypeScript, Tailwind, shadcn/ui, Recharts, TanStack Query; FastAPI, Python, SQLAlchemy 2, Alembic, Pydantic; PostgreSQL, pgvector; Docker, Docker Compose, Makefile.
**Последствия:** изменение библиотек/сервисов требует нового ADR; frontend/backend contracts формализуются OpenAPI.

## 4. ADR-002 — Local-first analytics

**Контекст:** данные чувствительны, запросы длинные, результат должен быть воспроизводимым.
**Решение:** validation, masking, embeddings, classification и clustering выполняются локально; LLM только формулирует bounded structured outputs.
**Последствия:** нужен local model benchmark; provider outage не уничтожает аналитику.

## 5. ADR-003 — Provider abstraction

**Контекст:** основной бюджетный provider — Gemini Flash через BotHub; нужны тесты и degradation.
**Решение:** единый typed interface с `BothubGeminiProvider`, deterministic `MockProvider` и optional `LocalProvider` adapter. Конкретный local runtime не фиксируется.
**Последствия:** domain logic не импортирует SDK; все adapters проходят одинаковые contract tests.

## 6. ADR-004 — Без H100

**Контекст:** пользователь уточнил ограничение исходного ТЗ.
**Решение:** H100 в v0.1.0 не используется; deployment и benchmark ориентированы на доступные CPU/обычные ресурсы и external API.
**Последствия:** модели и concurrency выбираются по resource measurements; GPU path требует нового ADR.

## 7. ADR-005 — Средний запрос 100k токенов

**Контекст:** пользователь подтвердил формулировку ТЗ как среднее, не maximum.
**Решение:** обязательны tokenizer-aware chunking, aggregation, streaming/batching и запрет silent truncation/full external transfer.
**Последствия:** dataset spike предшествует выбору моделей и limits; storage/performance budget выше обычного prompt analytics.

## 8. ADR-006 — PostgreSQL-backed jobs

**Контекст:** pipeline долгий, но добавление Redis/Celery нарушило бы минимальность стека.
**Решение:** worker claims jobs через PostgreSQL lease и `SKIP LOCKED`.
**Последствия:** меньше operational components; throughput достаточен только после benchmark, возможная замена — отдельный ADR post-MVP.

## 9. ADR-007 — CSV upload MVP

**Контекст:** нужен dataset/script submission и строгая file validation.
**Решение:** один CSV с canonical mapping; JSONL/XLSX/archive не поддерживаются.
**Последствия:** простой безопасный parser и demo; новый формат требует требований/security tests.

## 10. ADR-008 — Embedding model (Proposed)

**Критерии выбора:** языки dataset, лицензия, CPU performance, context/chunk behavior, semantic quality, vector dimension и reproducibility.
**Не принято:** название модели и library.
**Условие решения:** dataset profile и comparative benchmark.

## 11. ADR-009 — Classification (Proposed)

**Кандидатная форма:** embedding-based multi-label classifier/prototypes с explainable rules fallback.
**Не принято:** training method, calibrated thresholds и taxonomy labels beyond initial examples.
**Условие решения:** экспертная labeled sample и baseline.

## 12. ADR-010 — Clustering (Proposed)

**Требования:** noise support, reproducible parameters, acceptable CPU/memory, cluster diagnostics.
**Не принято:** algorithm/library/index type.
**Условие решения:** сравнение на reference dataset и expert grouping review.

## 13. ADR-011 — Production controls (Deferred)

**Отложено:** identity provider/SSO, detailed RBAC, retention, object storage, backups/DR, monitoring stack и SLA.
**Причина:** отсутствуют deployment owner/policies; Hackathon MVP предусматривает boundaries, но не заявляет production readiness.

## 14. Правило добавления ADR

ADR обязателен при изменении стека, trust boundary, external provider, data format, persistence, algorithm/model, authorization или deployment profile. Решение содержит контекст, варианты, последствия и migration impact.

## 15. Связанные документы

- [Architecture](./09-architecture.md)
- [AI Pipeline](./10-ai-pipeline.md)
- [Deployment](./17-deployment.md)
