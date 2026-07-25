# API

Arvexo Radar предоставляет versioned HTTP API с base path `/api/v1`. FastAPI OpenAPI после реализации будет machine-readable контрактом; текущая спецификация определяет ожидаемое поведение до написания кода.

Основные группы:

- system health/readiness;
- datasets, validation и masked preview;
- analysis runs, progress и executive overview;
- categories, scenarios, insights, prompt health и security findings;
- PDF report jobs/download.
- enterprise analytics: usage, models, agents, tools, departments, TCO, business effect и ROI;
- methodology/model tariffs/scenario benchmarks и Cost Component CRUD;
- Best Practice review/publish/recommend и Practice Adoption.

Все resources tenant-scoped. Create-run/report поддерживают idempotency, errors имеют безопасную schema и correlation ID, а rate limits возвращают `429` с `Retry-After`.

Полный список endpoints, examples и status codes: [docs/15-api.md](./docs/15-api.md).

Контракт Enterprise MVP и общие filters: [docs/24-enterprise-effectiveness.md](./docs/24-enterprise-effectiveness.md).
