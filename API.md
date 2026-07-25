# API

Arvexo Radar предоставляет versioned HTTP API с base path `/api/v1`. FastAPI OpenAPI после реализации будет machine-readable контрактом; текущая спецификация определяет ожидаемое поведение до написания кода.

Основные группы:

- system health/readiness;
- datasets, validation и masked preview;
- analysis runs, progress и executive overview;
- categories, scenarios, insights, prompt health и security findings;
- PDF report jobs/download.

Все resources tenant-scoped. Create-run/report поддерживают idempotency, errors имеют безопасную schema и correlation ID, а rate limits возвращают `429` с `Retry-After`.

Полный список endpoints, examples и status codes: [docs/15-api.md](./docs/15-api.md).

