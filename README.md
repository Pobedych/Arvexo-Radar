# Arvexo Radar

> Turn AI Conversations into Business Decisions.

Arvexo Radar — Enterprise AI Analytics Platform для анализа журналов запросов к корпоративным AI-агентам. Платформа классифицирует запросы, обнаруживает устойчивые use cases, объясняет результаты, выявляет prompt-health/security signals и формирует evidence-backed рекомендации для CTO и AI Platform Owner.

**Текущая версия:** v0.1.0 — Hackathon MVP
**Статус:** documentation-first; backend/frontend skeleton в разработке
**Целевой домен:** `radar.arvexo.ru`
**Исходный кейс:** КРОК

## Ключевые вопросы

1. Что происходит с использованием AI внутри организации?
2. Что руководству следует сделать дальше?

Radar показывает подтверждённые логами usage/proxy signals. Он не заявляет доказанный ROI без outcome-данных и не предназначен для оценки отдельных сотрудников.

## MVP flow

```text
Upload
→ Validation
→ Normalization
→ Sensitive Data Masking
→ Embeddings
→ Classification
→ Scenario Clustering
→ Scenario Naming and Summarization
→ Business Insights
→ Executive Dashboard
→ PDF Report
```

## Зафиксированный стек

- **Frontend:** Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Recharts, TanStack Query.
- **Backend:** FastAPI, Python, SQLAlchemy 2, Alembic, Pydantic.
- **Database:** PostgreSQL, pgvector.
- **Infrastructure:** Docker, Docker Compose, Makefile.
- **AI/ML:** local-first embeddings/classification/clustering; Gemini Flash через BotHub API для bounded generation; mock provider и подключаемый local test provider.

H100 в v0.1.0 не используется. Средний размер запроса по ТЗ принимается равным `100k токенов`, поэтому pipeline требует chunking без silent truncation.

## Документация

Документация — Single Source of Truth. Код реализуется только после утверждения соответствующей спецификации.

### Product

- [Vision](./docs/01-vision.md)
- [Business Problem](./docs/02-business-problem.md)
- [Stakeholders](./docs/03-stakeholders.md)
- [Personas](./docs/04-personas.md)
- [Product Goals](./docs/05-product-goals.md)
- [Non-goals](./docs/06-non-goals.md)
- [Functional Requirements](./docs/07-functional-requirements.md)
- [Dataset](./docs/08-dataset.md)

### Design and engineering

- [Architecture](./docs/09-architecture.md)
- [AI Pipeline](./docs/10-ai-pipeline.md)
- [Dashboard](./docs/11-dashboard.md)
- [Backend](./docs/12-backend.md)
- [Frontend](./docs/13-frontend.md)
- [Database](./docs/14-database.md)
- [API](./docs/15-api.md)
- [Security](./docs/16-security.md)
- [Deployment](./docs/17-deployment.md)

### Delivery

- [Roadmap](./docs/18-roadmap.md)
- [Demo Script](./docs/19-demo-script.md)
- [Judges FAQ](./docs/20-judges-faq.md)
- [Architecture Decisions](./docs/21-architecture-decisions.md)
- [CI/CD](./docs/22-ci-cd.md)

Краткие entry points: [ARCHITECTURE.md](./ARCHITECTURE.md), [SECURITY.md](./SECURITY.md), [API.md](./API.md), [DEMO.md](./DEMO.md), [ROADMAP.md](./ROADMAP.md).

## Исходные материалы

- [ТЗ кейса КРОК](./кейс%20КРОК%20__%20текст.pdf)

Примеры из ТЗ рассматриваются как темы запросов, а не как подтверждённый production dataset или разрешение на прямые интеграции.

## Локальный запуск

```bash
cp .env.example .env
make up
```

`api` контейнер применяет Alembic-миграции при старте. `worker` опрашивает `analysis_jobs` (`SELECT ... FOR UPDATE SKIP LOCKED`) и выполняет весь пайплайн анализа: embeddings → classification → clustering → scenario naming (LLM) → insights/recommendations (LLM). Полный контракт запуска — в [Deployment Specification](./docs/17-deployment.md).

Демонстрационный сквозной сценарий (`provider_mode=mock`, без внешних ключей):

```bash
curl -F file=@sample.csv http://localhost:8000/api/v1/datasets
curl -X POST http://localhost:8000/api/v1/datasets/{dataset_id}/runs \
  -H "Content-Type: application/json" -d '{"provider_mode":"mock"}'
curl http://localhost:8000/api/v1/runs/{run_id}
curl http://localhost:8000/api/v1/runs/{run_id}/overview
curl -X POST http://localhost:8000/api/v1/runs/{run_id}/reports
curl http://localhost:8000/api/v1/reports/{report_id}/download -o report.pdf
```

### Известные упрощения MVP (см. код для деталей)

- **Embeddings** — детерминированный hashing-векторизатор (`app/domain/embeddings.py`), не обученная семантическая модель; реальная локальная модель выбирается после аудита reference dataset (docs/10-ai-pipeline.md).
- **Classification** — keyword-fallback (`app/domain/classification.py`), объяснимый baseline, а не семантический классификатор.
- **Clustering** — жадная косинусная кластеризация (`app/domain/clustering.py`), плейсхолдер до выбора алгоритма по ADR (docs/09-architecture.md).
- **Chunking длинных запросов** (100k-token records) не реализован — каждая запись обрабатывается как один chunk.
- PDF-отчёт использует встроенный DejaVu Sans (для кириллицы); шрифт ставится в образ через `fonts-dejavu-core` (см. `backend/Dockerfile`).

## CI/CD

GitHub Actions: `ci.yml` (lint + pytest против реальной Postgres+pgvector + build-check образов) на каждый push/PR, `cd.yml` (publish в GHCR + SSH-деплой на `main`) — после того как CI на этом же commit прошёл. Подробности, требуемые secrets и диагностика сбоев — в [docs/22-ci-cd.md](./docs/22-ci-cd.md).

## Участие в разработке

Правила изменений, тестирования, безопасности и документации приведены в [CONTRIBUTING.md](./CONTRIBUTING.md). История версии — в [CHANGELOG.md](./CHANGELOG.md).

## Лицензия

Проект не распространяется по open-source лицензии. См. [LICENSE](./LICENSE).
