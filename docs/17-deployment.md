# Arvexo Radar: deployment

**Версия:** v0.1.0 — Hackathon MVP
**Стек:** Docker, Docker Compose, Makefile

## 1. Deployment profiles

### `demo`

Локальный запуск, demo principal, mock provider по умолчанию, synthetic/reference dataset. Не предназначен для публичного доступа.

### `api`

Локальный/защищённый запуск с BotHub API key, теми же контейнерами и явной provider configuration.

### `production` (архитектурно предусмотрен)

Требует HTTPS, authentication adapter, secret management, encrypted storage, retention и backup policy. Полная production readiness не входит в v0.1.0.

## 2. Compose services

- `web`: Next.js application;
- `api`: FastAPI HTTP process;
- `worker`: backend analysis worker;
- `db`: PostgreSQL с pgvector;

Named volumes: database data, controlled datasets/reports, local model cache. Ports наружу минимальны; DB не публикуется в production profile.

## 3. Configuration

Пример имён без значений:

```dotenv
APP_ENV=demo
AUTH_MODE=demo
DATABASE_URL=postgresql+...
STORAGE_ROOT=/data
LLM_PROVIDER=mock
BOTHUB_API_URL=
BOTHUB_API_KEY=
BOTHUB_MODEL=
LOCAL_LLM_URL=
MAX_UPLOAD_BYTES=
MAX_ROW_CHARS=
WORKER_CONCURRENCY=
```

`.env.example` после начала реализации содержит только безопасные placeholders. `.env` и keys не коммитятся.

## 4. Makefile contract

Планируемые команды:

```text
make setup      # подготовить безопасную локальную конфигурацию
make up         # build/start services
make down       # stop services без удаления volumes
make migrate    # apply Alembic migrations
make test       # backend/frontend tests
make lint       # static checks
make logs       # safe service logs
make demo       # start deterministic demo profile
```

Команда удаления volumes не включается в обычный flow и, если появится, требует явного destructive имени/подтверждения.

## 5. Startup order и readiness

DB healthy → migrations completed → API/worker ready → web ready. Liveness не зависит от внешнего LLM; readiness сообщает provider degradation отдельно, чтобы mock/local analytics оставались доступны.

## 6. Local model assets

Model identifier/version конфигурируется. Download не должен происходить неожиданно при каждом старте. Для offline demo образ/volume предварительно подготавливается документированной командой; лицензия модели проверяется до распространения.

## 7. Resource planning

H100 не используется. CPU/RAM/disk budget измеряется на reference dataset со средним запросом 100k токенов. Concurrency defaults выбираются после замеров; OOM не маскируется retry loop. GPU acceleration, если когда-либо появится, требует отдельного ADR.

## 8. Migrations и rollback

Deploy применяет Alembic до приема traffic. Application version должна быть совместима с migration state. Rollback контейнера не откатывает destructive DB migration автоматически; для таких изменений нужен backup/restore plan.

## 9. Backup и retention

Demo backup не обязателен. Production требует согласованные PostgreSQL/storage backup, encryption, restore test и retention. Значения не фиксируются без владельца данных.

## 10. Target domain

Целевой домен — `radar.arvexo.ru`. DNS, certificates и hosting provider не выбраны. Документация не утверждает, что домен уже развёрнут.

## 11. Demo runbook

1. Проверить Docker/Compose и свободные resources.
2. Создать config из example без реальных данных в Git.
3. Запустить `make up`/`make demo`.
4. Применить migrations.
5. Проверить `/health` и `/ready`.
6. Загрузить reference dataset и пройти [Demo Script](./19-demo-script.md).
7. Проверить PDF download.
8. Остановить через `make down`, сохранив volumes.

## 12. Acceptance criteria

- **DEP-AC-01:** clean machine запускает demo по README.
- **DEP-AC-02:** mock mode не требует API key.
- **DEP-AC-03:** key отсутствует в image, logs и frontend.
- **DEP-AC-04:** restart worker продолжает safe queued jobs.
- **DEP-AC-05:** migration создаёт pgvector schema.
- **DEP-AC-06:** внешний provider outage не делает API unhealthy.

## 13. Связанные документы

- [Architecture](./09-architecture.md)
- [Security](./16-security.md)
- [Demo Script](./19-demo-script.md)
- [CI/CD](./22-ci-cd.md)
