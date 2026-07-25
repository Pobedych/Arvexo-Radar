# Arvexo Radar: backend

**Версия:** v0.1.0 — Hackathon MVP
**Стек:** FastAPI, Python, SQLAlchemy 2, Alembic, Pydantic

## 1. Структура

```text
backend/
  app/
    api/            # routers, dependencies, error mapping
    application/    # use cases and orchestration
    domain/         # entities, value objects, policies
    repositories/   # ports
    services/       # ML, LLM, masking, reports ports
    infrastructure/ # SQLAlchemy, storage, provider adapters
    schemas/        # Pydantic request/response/provider schemas
    worker/         # job claim and execution
    config.py
    main.py
  alembic/
  tests/
```

Финальные имена могут меняться без изменения границ слоёв.

## 2. Coding contracts

- Python type hints обязательны для public functions.
- Pydantic валидирует все boundary inputs/outputs.
- SQLAlchemy 2 используется в typed declarative style.
- Raw SQL допустим для pgvector/jobs только через параметризованные statements.
- Domain errors типизированы; broad exception не маскируется как success.
- Async/sync mode выбирается единообразно; смешение session patterns запрещено.

## 3. Application services

- `CreateDataset`
- `ValidateDataset`
- `CreateAnalysisRun`
- `ExecuteAnalysisStage`
- `GetExecutiveOverview`
- `GetCategory/ScenarioDetail`
- `GenerateReport`

Каждый use case проверяет authorization context, transaction boundary и idempotency.

## 4. File handling

Upload читается streaming с byte limit, сохраняется под server-generated name вне public path и не доверяет client filename. Parser работает в worker после первичной проверки. Ошибки не включают строку целиком.

## 5. Job execution

`analysis_jobs` хранит stage, attempts, lease owner/time, available_at и error code. Worker claims job через PostgreSQL locking, обновляет heartbeat и делает stage idempotent. Истёкшая lease допускает повторный claim; side effects должны быть upserted по run/stage/version.

## 6. Transactions

- короткие DB transactions;
- model/API calls вне открытой transaction;
- stage writes атомарны;
- completed run immutable;
- report job ссылается на persisted result snapshot.

## 7. LLM adapters

Общий protocol принимает typed operation/evidence и возвращает typed result/provenance. API key читается из environment/secret injection, никогда из request body. Provider payload строится только из masked data.

## 8. Error model

Application error имеет `code`, safe `message`, `status`, `retryable`, `details` без sensitive content и `correlation_id`. Traceback доступен только server logs и также не должен содержать dataset text/provider payload.

## 9. Configuration

Pydantic Settings загружает environment values: DB URL, storage path, file/token limits, provider mode, BotHub endpoint/model/key, timeouts, retry/cache settings, auth mode и rate limits. Startup валидирует обязательные параметры выбранного mode.

## 10. Testing

- unit: normalization, masking, validation, thresholds, state transitions;
- property/fuzz: CSV parser boundaries и masking leakage;
- integration: PostgreSQL/pgvector repositories, job claiming, API contracts;
- provider contract: mock/API/local adapters на одинаковых schemas;
- e2e backend: upload → run → results → report metadata;
- security regression: CSV Injection, secrets in logs/output, IDOR boundaries.

Нельзя заявлять результаты тестов до их фактического запуска.

## 11. Acceptance criteria

- routers не содержат domain calculations;
- no raw text in logs/errors;
- job restart не дублирует results;
- provider swap не меняет application service;
- migrations создают schema с нуля и обновляют предыдущую version;
- mock mode работает без external credentials.

## 12. Связанные документы

- [Architecture](./09-architecture.md)
- [Database](./14-database.md)
- [API](./15-api.md)
- [Security](./16-security.md)

