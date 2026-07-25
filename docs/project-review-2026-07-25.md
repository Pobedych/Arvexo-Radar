# Полное техническое ревью Arvexo Radar

**Дата ревью:** 25 июля 2026 года  
**Проверенное состояние:** текущая рабочая директория, включая незакоммиченные файлы

## Итог

Проект уже выглядит как сильный, целостный Enterprise MVP и хорошо подходит для демонстрации продукта. Основные пользовательские сценарии, UI, локальный аналитический pipeline, телеметрия, Best Practices, ROI-формулы, PDF и инфраструктурный каркас действительно реализованы.

Но production-ready системой Radar пока не является. Главные блокеры: отсутствие реальной аутентификации и tenant context, подмена ошибок демонстрационными данными, неподключённое persistence для Enterprise Analytics, проблемы надёжности worker, незавершённые LLM-adapter’ы и критические уязвимости текущей версии Next.js.

Моя оценка зрелости:

| Область | Оценка |
|---|---:|
| Product/demo readiness | 8/10 |
| Backend foundation | 7/10 |
| Формулы TCO/ROI | 8/10 |
| Frontend/dashboard | 7/10 |
| Автотесты | 6/10 |
| Production data path | 3/10 |
| Security/IAM | 2/10 |
| Operations/reliability | 4/10 |

Условно: демонстрационный MVP готов примерно на 75–80%, production-платформа — на 30–40%.

## Состояние репозитория

Текущий `main` совпадает с `origin/main`, последний коммит — `852d399`, но поверх него находится большой рабочий слой:

- 26 изменённых файлов;
- 30 untracked-файлов;
- всего 56 незакоммиченных файлов;
- tracked diff: `+706 / -63`, без учёта новых файлов.

Именно в uncommitted-слое находятся Enterprise Analytics, Best Practices, proxy telemetry, TCO/ROI, новые миграции и тесты. То есть фактический текущий проект значительно продвинутее состояния Git, но ещё не является воспроизводимой версией для CI/CD или другого разработчика.

Объём:

- backend application: 71 Python-файл, около 7 541 строк;
- backend tests: 15 файлов, около 1 229 строк;
- frontend: около 2 364 строк TS/TSX/CSS;
- документация: 25 документов, около 3 814 строк.

## Что уже реализовано

### 1. Архитектурная основа

Есть понятный modular monolith:

```text
Next.js UI
   ↓
FastAPI API
   ↓
Application/domain services
   ↓
SQLAlchemy + PostgreSQL/pgvector
   ↓
Отдельный polling worker
```

Хорошо разделены:

- API routers;
- application use cases;
- чистые domain calculations;
- repositories;
- infrastructure adapters;
- worker process;
- schemas и migrations.

Композиция API находится в `backend/app/main.py`. Сейчас OpenAPI содержит 43 path и около 48 операций.

### 2. Dataset ingest

Работает полный базовый ingest:

- multipart upload;
- ограничение размера;
- CSV с `,`, `;`, tab;
- canonical mapping полей;
- коды ошибок V001–V009;
- нормализация текста;
- маскирование email, телефонов и некоторых секретов;
- masked preview;
- дедупликация по checksum;
- сохранение validation summary;
- создание records.

Основная реализация — `backend/app/domain/dataset_validation.py` и `backend/app/application/create_dataset.py`.

Сильная сторона: в аналитическую часть передаётся `masked_text`, а клиентское имя файла не используется как filesystem path.

### 3. Аналитический pipeline

Реализована последовательность:

```text
Records
→ hashing embeddings
→ keyword classification
→ greedy clustering
→ representative samples
→ scenario naming
→ Best Practice detection
→ prompt/security findings
→ insights
→ recommendations
```

Pipeline реально создаёт `Classification`, `Scenario`, `ScenarioMember`, `Finding`, `Insight`, `Recommendation` и Best Practice. Главная оркестрация — `backend/app/application/execute_analysis_run.py`.

Текущие алгоритмы честно обозначены как baseline:

- embeddings — hashing bag-of-words;
- classification — keyword matching;
- clustering — greedy cosine;
- generation — mock provider.

Это правильный подход для демонстрации без притворства, что уже построена production ML-система.

### 4. Best Practices

Реализованы:

- Impact Score;
- Confidence Score;
- пороговые правила;
- обязательность rating/success signals;
- обнаружение кандидатов;
- workflow `detected → under_review → approved → published`;
- recommendation и adoption;
- группировки TOP/new/growing/effective;
- DB-модель и repository;
- demo implementation.

Особенно хорошо сделана чистая и тестируемая логика в `backend/app/domain/best_practices.py`.

### 5. TCO, ROI и business effect

Есть чистая Decimal-based реализация:

- token cost;
- shared cost allocation;
- time saved;
- FTE equivalent;
- money saved;
- net benefit;
- ROI;
- payback;
- insufficient-data status;
- нормализация FTE по длительности периода.

Код в `backend/app/domain/effectiveness.py` выглядит одним из самых зрелых фрагментов проекта. Формулы покрыты хорошими unit-тестами.

### 6. LLM proxy и телеметрия

Реализован OpenAI-compatible endpoint:

- обычные и streaming response;
- passthrough provider payload;
- content-free telemetry;
- salted hash пользователя;
- latency и TTFT;
- token usage;
- effective-dated tariff;
- классификация ошибок;
- safe error messages;
- SSE parser без хранения ответа.

Основные файлы:

- `backend/app/api/routers/proxy.py`;
- `backend/app/services/analytics_telemetry.py`;
- `backend/app/infrastructure/providers/openai_proxy.py`.

### 7. Dashboard

Frontend уже представляет собой полноценный демонстрационный продукт:

- overview;
- effectiveness;
- agents;
- departments;
- tools/sources;
- Best Practices;
- Knowledge Discovery;
- insights;
- methodology editor;
- filters;
- CSV export;
- responsive sidebar;
- demo-data warning.

Визуально и продуктово frontend значительно ближе к готовому MVP, чем backend Enterprise persistence.

### 8. PDF и инфраструктура

Есть:

- PDF с кириллицей и DejaVu Sans;
- Alembic chain `0001 → 0005`;
- Docker Compose для dev и production;
- loopback-only production ports;
- nginx;
- CI с lint, tests, migrations и Docker build;
- CD в GHCR и SSH deploy;
- smoke tests.

## Результаты проверок

На текущем, включая незакоммиченные файлы, состоянии:

- `pytest`: 85 тестов прошли;
- Ruff: прошёл;
- ESLint: прошёл;
- TypeScript/Next production build: прошёл;
- Alembic: один корректный head `0005`;
- dev Docker Compose config: валиден;
- `git diff --check`: ошибок нет.

Next build выдал предупреждение о невалидном Windows SWC binary, но успешно завершился через fallback. Это локальная проблема установленного `node_modules`, не ошибка исходного кода.

## Критические блокеры

### P0. Production запускается без аутентификации

`auth_mode` объявлен, но нигде фактически не применяется. Principal всегда равен `"demo-user"`:

- `backend/app/config.py`;
- `backend/app/api/deps.py`.

Проверка показала: `Settings(environment="production", auth_mode="demo", ...)` успешно создаётся. То есть требование «production fail closed» сейчас не выполнено.

Дополнительно:

- большая часть endpoints вообще не зависит от `get_current_principal`;
- tenant захардкожен как `DEMO_TENANT_ID`;
- methodology и cost CRUD доступны без authorization;
- Best Practice approve/publish/adoption доступны без ролей;
- proxy не требует Radar authentication.

При публичном размещении `/api/*` это блокер эксплуатации.

### P0. Production API может возвращать вымышленные показатели как реальные

`backend/app/api/routers/analytics.py` сначала строит demo payload, затем пытается добавить live-показатели.

Опасные случаи:

- ошибка PostgreSQL проглатывается;
- пустой production DB считается отсутствием данных и заменяется demo-числами;
- `total_requests == 0` приводит к подстановке 28 400 запросов;
- `/errors` возвращает фиксированные 594/386 ошибок;
- `/models` при пустом результате возвращает demo models;
- `/usage` может содержать live summary и demo items одновременно;
- agents/tools/departments/costs/ROI полностью demo независимо от environment.

Frontend дополнительно перехватывает любую ошибку и возвращает fallback в `frontend/lib/enterprise.ts`.

Баннер показывается, но для executive analytics этого недостаточно: HTTP 500, авторизационная ошибка и отсутствие данных превращаются в успешный экран с убедительными цифрами. Это прямо противоречит требованию в `docs/12-backend.md`.

### P0. Уязвимая версия Next.js

`npm audit --omit=dev` сообщил:

- 1 critical;
- 2 high;
- затронуты `next@15.0.3`, его `postcss` и `sharp`.

Audit перечисляет RCE/DoS/cache/SSRF-related advisories. До публичной эксплуатации Next необходимо обновить и повторить build/audit/regression tests.

## Высокие риски

### P1. Enterprise persistence создано в БД, но не подключено к API

Таблицы `cost_components`, `methodology_settings`, `scenario_benchmarks`, `practice_adoptions` существуют, но Methodology/Cost API работает с singleton в памяти: `backend/app/services/enterprise_analytics.py`.

Следствия:

- изменения пропадают после restart;
- несколько API replicas имеют разное состояние;
- seed-данные БД не читаются API;
- production environment всё равно получает in-memory adapter;
- нет optimistic locking/version history/audit trail.

Best Practice persistence подключено лучше, но всё равно используется hardcoded demo tenant.

### P1. Tenant model неполный

Без `tenant_id` созданы:

- `llm_request_events`;
- `model_tariffs`;
- `cost_components`;
- `scenario_benchmarks`;
- `tool_usages`.

Analytics repository агрегирует все события общей таблицы. В реальном multi-tenant развёртывании данные компаний смешаются.

### P1. Readiness возвращает HTTP 200 при неготовности

`backend/app/api/routers/system.py` возвращает:

```json
{"status":"not_ready","database":"unavailable"}
```

но со статусом HTTP 200. Это было воспроизведено при выключенной БД.

Поэтому `curl -f` в CD считает контейнер готовым, даже если PostgreSQL недоступен. Следует возвращать 503 и проверять storage/provider readiness.

### P1. Worker lease фактически не восстанавливается

`claim_next_job()` выбирает только `status == pending` в `backend/app/repositories/analysis_repository.py`.

При падении worker:

- job останется `running`;
- истёкший `lease_expires_at` не используется;
- heartbeat не обновляется;
- retry/backoff/max attempts отсутствуют;
- job больше никогда не будет выбран.

При добавлении reclaim pipeline также нужно сделать stage-level idempotent: текущие bulk insert могут столкнуться с уже сохранёнными classifications/scenarios.

### P1. Реальные LLM provider modes не реализованы

Конфигурация предлагает `mock`, `bothub`, `local`, но factory поддерживает только mock: `backend/app/infrastructure/providers/factory.py`.

При `bothub` или `local` worker падает с `NotImplementedError`.

Кроме того, `provider_mode` из create-run сохраняется в snapshot, но worker выбирает provider только из глобальных settings. Таким образом, per-run provider mode сейчас декоративный.

### P1. Telemetry находится на критическом пути ответа LLM

После успешного ответа provider route сначала ждёт сохранения telemetry в PostgreSQL, и только затем возвращает ответ.

Если DB недоступна:

- успешный non-stream LLM request превращается в HTTP 500;
- streaming response может оборваться после уже отправленных токенов;
- telemetry outage становится LLM gateway outage.

Нужен bounded buffer/outbox/async writer либо по крайней мере fail-open режим для telemetry с отдельной метрикой потерь.

### P1. `/v1/chat/completions` не маршрутизируется production nginx

Nginx отправляет в API только `/api/`, а всё остальное — во frontend: `deploy/nginx/radar.arvexo.ru.conf`.

Поэтому публичный `/v1/chat/completions` сейчас попадёт в Next.js. Если добавить location для `/v1/`, предварительно обязательно нужны authentication и rate limiting, иначе получится открытый proxy на корпоративный API key.

### P1. Смешанные timestamp могут уронить worker

`datetime.fromisoformat()` принимает одновременно naive и timezone-aware значения и не приводит их к UTC. Затем `_growth_rate()` сортирует timestamp.

Воспроизведён результат:

```text
TypeError: can't compare offset-naive and offset-aware datetimes
```

Это способно перевести весь run в `PIPELINE_EXECUTION_FAILED`.

### P1. Pipeline не масштабируется к заявленному объёму

Основные причины:

- `UploadFile.read()` сначала читает весь файл в память, ограничение проверяется после этого;
- CSV полностью декодируется в одну строку;
- все `RowResult` сохраняются в список;
- все embeddings находятся в памяти;
- greedy clustering сканирует существующие кластеры;
- при каждом добавлении пересчитывается centroid по всем участникам;
- chunking 100k-token records отсутствует;
- pipeline выполняется одной длинной транзакционной последовательностью.

Граф кода показывает `ExecuteAnalysisRun.execute` как главный hotspot: 242 строки, cyclomatic complexity 18, cognitive complexity 33.

## Средние риски и технический долг

### API и contracts

- Runtime/OpenAPI version всё ещё `0.1.0`, README заявляет `v0.3.0`.
- Backend/frontend packages также `0.1.0`.
- CHANGELOG всё ещё говорит, что `0.1.0` planned и реализация отсутствует.
- Основной API versioned через `/api/v1`, Enterprise API — `/api`, analytics — `/api/analytics`, proxy — `/v1`: контракт фрагментирован.
- Многие Enterprise endpoints возвращают `dict[str, Any]`, поэтому OpenAPI почти не описывает реальные response schemas.
- Report endpoint возвращает 202, но синхронно строит PDF до ответа.
- Rate limit setting существует, middleware/limiter отсутствует.
- Unexpected exception handler не логирует traceback.
- Correlation ID появляется только в error response, а не проходит через весь request lifecycle.

### Frontend

- `frontend/components/EnterpriseViews.tsx` — 1 172 строки.
- Нет frontend unit/component/e2e tests.
- Нет Error Boundary.
- Mutation methodology использует тот же fallback helper, поэтому сетевая ошибка выглядит как успешное сохранение.
- Recommend для demo practice только локально меняет статус.
- Footer содержит жёстко заданные «6 подразделений / 4 сценария / 4 агента» независимо от filters/API.
- Все справочники фильтров захардкожены.

### Database и data integrity

- Нет repository integration tests против PostgreSQL.
- CI применяет миграции к реальной БД, но сами queries выполняются через fakes/demo adapter.
- Нет foreign-key cascade policy и retention/deletion workflow.
- Raw CSV сохраняется на файловый volume без application-level encryption.
- `ToolUsage` таблица есть, но recorder сохраняет только JSON `tool_calls`; отдельные tool rows не создаются.
- Idempotency реализована check-then-insert, поэтому конкурентные одинаковые запросы могут закончиться unique violation вместо корректного reuse.

### Docker/CI/CD

Плюсы: loopback production ports, отдельные images, migration gate, SHA deploy, smoke tests.

Недочёты:

- frontend Dockerfile игнорирует существующий lockfile и использует `npm install`;
- CI-комментарий утверждает, что lockfile ещё не committed, хотя он присутствует;
- backend не имеет lock/constraints;
- backend production image устанавливает dev dependencies и копирует tests;
- контейнеры запускаются под root;
- API/web не имеют container healthcheck;
- readiness smoke test сейчас ложноположительный из-за HTTP 200;
- Docker build не фиксирует воспроизводимые dependency versions.

## Тестовая зрелость

85 проходящих тестов — хороший результат для текущего размера, особенно покрыты:

- CSV validation;
- masking;
- normalization;
- classification;
- clustering;
- PDF;
- prompt health;
- proxy/SSE telemetry;
- TCO/ROI formulas;
- Best Practice scoring;
- часть API contract.

Критически отсутствуют:

- fresh-DB repository CRUD tests;
- tenant isolation/IDOR tests;
- production auth fail-closed tests;
- worker crash/lease/retry tests;
- полный upload → worker → report end-to-end;
- реальные migrations + queries;
- telemetry DB outage;
- concurrent idempotency;
- mixed timestamp regression;
- frontend component/e2e/accessibility tests;
- performance tests на reference dataset;
- coverage threshold.

## Рекомендованный порядок работ

### Этап 0 — зафиксировать текущее состояние

1. Разделить 56 изменений на логические commits.
2. Добавить все новые migrations/source/tests.
3. Синхронизировать README, CHANGELOG, package/runtime versions.
4. Прогнать CI уже на commit, а не только локально.

### Этап 1 — production blockers

1. Реализовать authenticated principal с `tenant_id` и permissions.
2. Запретить `environment=production + auth_mode=demo/none`.
3. Добавить auth ко всем resource/config/workflow endpoints.
4. Полностью запретить demo fallback вне demo environment.
5. Возвращать явные `503/no_data/degraded`, а не synthetic показатели.
6. Обновить Next.js и повторить `npm audit`.
7. Исправить readiness на HTTP 503.
8. Добавить tenant ownership в telemetry, tariffs, costs и benchmarks.

### Этап 2 — настоящий Enterprise data path

1. Подключить DB repositories к methodology/costs/benchmarks.
2. Разделить demo и production service implementations.
3. Построить agents/tools/departments/business-effect из live tables.
4. Добавить provenance на уровне каждого показателя.
5. Перестать смешивать live summary и demo detail.
6. Реализовать HR/FinOps/outcome adapters либо честный `integration_required`.

### Этап 3 — надёжность pipeline

1. Reclaim expired leases.
2. Heartbeat и bounded retries.
3. Idempotent stage writes.
4. Chunking длинных records.
5. Batch processing и ограничение памяти.
6. Исправить UTC normalization.
7. Проверить BotHub structured responses, разделить причины provider errors и реализовать local adapter.
8. Использовать provider snapshot конкретного run.
9. Убрать telemetry DB с критического пути LLM.

### Этап 4 — эксплуатационная зрелость

1. Structured logs, metrics, tracing и audit log.
2. Backup/restore и retention policy.
3. Object storage вместо локального volume.
4. Non-root/minimal production containers.
5. Lockfiles/constraints и dependency scanning.
6. E2E, security и performance gates.

## Финальный вывод

Сильнейшая часть проекта — не отдельный алгоритм, а целостность демонстрационного продукта: документация, бизнес-логика, UI, формулы и storytelling хорошо согласованы. Это уже можно показывать как Enterprise Effectiveness MVP, если явно говорить, что аналитика работает на coherent demo dataset.

Основная проблема сейчас — граница между demo и production слишком размыта технически. Backend способен запускаться в production-конфигурации, оставаясь demo-системой, а при ошибках может показать синтетические показатели как успешный ответ. Поэтому следующий правильный этап — не добавление новых экранов, а hardening существующего вертикального среза: auth, tenant isolation, live persistence, честные degraded states и worker reliability.

## Дополнение: production E2E на radar.arvexo.ru

Проверка выполнена 25 июля 2026 года через публичный UI и API без Docker. Использован синтетический CSV из 21 строки с тремя группами запросов: почта, управленческая отчётность и планирование проектов.

### Что прошло

- `health` и `ready` отвечают HTTP 200, база помечена как `ok`;
- CSV загружается, dataset создаётся и проходит валидацию;
- принято 20 строк без замечаний и 1 с предупреждением, отклонено 0;
- email в evidence замаскирован как `[EMAIL_1]`;
- локальная классификация, кластеризация, findings и insights рассчитываются;
- drill-down категорий и сценариев возвращает masked samples;
- PDF создаётся и скачивается: 29 671 байт, сигнатура `%PDF-`, SHA-256 совпадает с checksum API;
- экраны «Эффективность ИИ», «AI-агенты», «Подразделения», «Инсайты», «Источники данных» и «Настройки методики» загружают данные без UI-ошибок.

Контрольный dataset: `ae88be8c-e3ad-4336-b217-32ac5693255f`. Контрольный run: `a9d280a7-2702-4f78-9acb-e755463eebc4`. Контрольный report: `70de74da-555f-4656-907a-7975a6d36e0f`.

### Метрики загруженного датасета

- записей: 21;
- топ-категория: «Отчётность и аналитика» — 15, или 71,4%;
- ещё три категории имеют по 7 срабатываний, доли пересекаются из-за multi-label классификации;
- устойчивые сценарии: 7, 7 и 4 записи; ещё 3 записи попали в noise;
- security findings: 1 `SEC_SENSITIVE_DATA` средней серьёзности;
- prompt-health findings: 0;
- insights: 7;
- recommendations: 0.

### P0: UI всегда теряет результат из-за таймаута

Два последовательных запуска через публичный UI завершились одинаково: после примерно 120 секунд модалка показывает «Анализ не завершился за отведённое время». При этом backend продолжает работу и позже переводит run в `degraded/completed`.

После закрытия модалки результат невозможно открыть:

- «Обзор» снова показывает «Пока нет статистики»;
- «Отчёты» показывает «Нет активного прогона анализа»;
- завершённый run и созданный PDF не появляются в истории;
- постоянной ссылки или восстановления последнего run нет.

Таким образом, полный путь «загрузка → просмотр метрик» через один только UI в production сейчас не проходит, хотя результаты доступны через API.

### P0: BotHub подключён, но Radar теряет точную причину LLM-деградации

История BotHub подтверждает успешные обращения к `gemini-2.5-flash` во время повторного UI-прогона 25 июля 2026 года примерно в 16:41:50–16:42:13. Следовательно, production key, авторизация и сетевой путь до BotHub работают.

Контрольный run при этом завершился с шестью деградациями `LLM_PROVIDER_UNAVAILABLE`: три для именования сценариев и три для генерации рекомендаций. `provenance` остался пустым, сценарии получили fallback-названия «Кластер 0/3/4», descriptions и recommendations отсутствуют.

Название ошибки неточное. `BothubProvider` превращает в общий `LLMProviderError` не только transport/HTTP failures, но также пустой ответ, невалидный JSON и несоответствие Pydantic-схеме. `ExecuteAnalysisRun` затем без различения записывает любой такой сбой как `LLM_PROVIDER_UNAVAILABLE`. Поэтому успешное списание в BotHub не доказывает, что Radar принял и сохранил структурированный ответ.

Нужно разделить как минимум `LLM_TIMEOUT`, `LLM_HTTP_ERROR`, `LLM_INVALID_JSON` и `LLM_SCHEMA_VALIDATION_FAILED`, сохраняя безопасные технические детали в server logs. После этого повторить прогон и проверить фактический ответ `gemini-2.5-flash` на совместимость с ожидаемой JSON-схемой.

### P1: два несвязанных контура метрик

Загруженный CSV обрабатывается `/api/v1/runs/*`, а executive dashboard получает отдельный coherent demo dataset из `/api/analytics/*`. В production UI видны, например, 28 400 запросов, 642 MAU, 379 млн токенов, 1 170 000 ₽ затрат и ROI 93,9%, но эти числа не относятся к загруженным 21 строкам. API прямо маркирует этот набор как `data_mode: demo`.

«Лучшие практики» также не связаны с завершённым run: экран и API возвращают 0 практик, несмотря на найденные сценарии. Это нужно явно объяснить на защите либо соединить контуры.

### P2: краткий 502 после генерации PDF

Сразу после успешного `POST /reports` один запрос метаданных и один download получили `502 Bad Gateway`. Повторная проверка вернула HTTP 200, PDF скачался и прошёл checksum. Это похоже на кратковременную нестабильность API/nginx; дефект не блокирующий, но его стоит проверить по production logs.

### Приоритет до дедлайна

1. Исправить UI polling: не обрывать анализ на 120 секундах, показывать run id, позволять продолжить ожидание и восстановить последний run после reload.
2. BotHub уже подключён; исправить диагностику LLM-ошибок и добиться сохранения naming/summary/recommendations без degraded fallback.
3. Добавить историю run/report и открыть уже завершённый результат из «Источников данных» или «Отчётов».
4. Чётко разделить в интерфейсе «анализ загруженного CSV» и «Enterprise demo analytics».
5. Проверить причину краткого 502 вокруг report download.
