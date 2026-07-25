# Architecture

Arvexo Radar использует modular monolith с отдельными process types: Next.js web, FastAPI API, Python analysis worker и PostgreSQL/pgvector. Docker Compose обеспечивает локальное развёртывание.

Ключевые решения:

- local-first validation, masking, embeddings, classification и clustering;
- внешний LLM только через provider abstraction и masked evidence;
- BotHub/Gemini Flash API, deterministic mock и optional local test adapter;
- PostgreSQL-backed jobs без дополнительного message broker;
- immutable analysis runs и полное model/config/evidence provenance;
- обязательный chunking для среднего запроса 100k токенов;
- H100 не используется.
- content-free LLM gateway telemetry является фактическим системным источником;
- pure Decimal calculation domain отделён от demo/DB adapters;
- TCO/Benchmark/Methodology и Adoption — отдельные persistence entities;
- full enterprise dashboard в demo-mode использует явно помеченный coherent synthetic adapter.

Полная спецификация, diagrams, trust boundaries и reliability model: [docs/09-architecture.md](./docs/09-architecture.md).

Связанные документы:

- [AI Pipeline](./docs/10-ai-pipeline.md)
- [Backend](./docs/12-backend.md)
- [Database](./docs/14-database.md)
- [Architecture Decisions](./docs/21-architecture-decisions.md)
- [Enterprise Effectiveness](./docs/24-enterprise-effectiveness.md)
