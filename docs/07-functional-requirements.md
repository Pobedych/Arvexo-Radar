# Arvexo Radar: функциональные требования

**Версия:** v0.1.0 — Hackathon MVP
**Статус:** спецификация для реализации

## 1. Область действия

Документ определяет поведение MVP. Приоритеты: **P0** — обязательный demo flow, **P1** — обязательное качество продукта при наличии данных, **P2** — после MVP.

## 2. Общие правила

- Любой аналитический результат связан с `dataset_id`, `analysis_run_id` и версией конфигурации.
- Исходный sensitive text не попадает в application logs и внешний LLM.
- Ошибка одного этапа не представляется как пустой корректный результат.
- Факт, гипотеза и рекомендация различаются типом.
- Расчёты dashboard и PDF используют один сохранённый result set.

## 3. Dataset Upload и Validation

### FR-UPL-01 — Загрузка dataset (P0)

Пользователь загружает один CSV-файл через UI. Сервер проверяет расширение, MIME/signature consistency, кодировку, размер по конфигурируемому лимиту и запрещает архивы/исполняемые файлы.

**Acceptance criteria:** неподдерживаемый или превышающий лимит файл отклонён до анализа; ошибка не содержит исходный текст; успешная загрузка создаёт dataset со статусом `uploaded`.

### FR-UPL-02 — Сопоставление полей (P0)

Обязательное каноническое поле — `text`; остальные поля опциональны. Если заголовки отличаются, пользователь или preset сопоставляет их с canonical schema до запуска.

### FR-VAL-01 — Построчная validation (P0)

Система проверяет наличие текста, типы, timestamp, дубликаты идентификаторов и технические ограничения. Результат содержит counts и безопасные причины отклонения.

### FR-VAL-02 — Preview (P0)

До анализа показываются только маскированные preview rows, состав полей, количество принятых/отклонённых строк и warnings.

### FR-VAL-03 — Частично валидный dataset (P0)

Пользователь может запустить анализ валидных строк, если есть хотя бы одна, а исключённые строки сохраняются только как безопасные validation records. Полностью невалидный dataset не запускается.

## 4. Normalization и Sensitive Data Masking

### FR-NRM-01 — Нормализация (P0)

Система нормализует Unicode, переносы строк и технический whitespace, не меняя смысл текста. Исходная и нормализованная версии логически разделены.

### FR-MSK-01 — Маскирование (P0)

До embeddings, samples и внешней передачи выявляются email, телефоны, API keys и распространённые secret patterns. Значения заменяются стабильными типизированными placeholders в пределах записи.

### FR-MSK-02 — Безопасный output (P0)

UI, PDF, API errors и application logs не возвращают найденное значение секрета. Finding содержит тип, severity, location metadata и masked preview.

### FR-MSK-03 — CSV Injection (P0)

Значения, начинающиеся с `=`, `+`, `-` или `@`, обезвреживаются при любом CSV/Excel-совместимом экспорте. Исходный текст не исполняется и не интерпретируется как формула.

## 5. Embeddings и длинные запросы

### FR-EMB-01 — Chunking (P0)

Запросы обрабатываются с учётом среднего размера `100k токенов`: текст делится ограниченными chunks с детерминированными границами и сохраняемой связью с исходной записью.

### FR-EMB-02 — Агрегация представления (P0)

Record embedding формируется из chunk embeddings по версионированной стратегии. Нельзя молча обрезать текст до model limit.

### FR-EMB-03 — Cache (P0)

Embedding cache keyed by sanitized content hash, model version и chunking version. Cache не хранит исходный текст в ключе.

## 6. Classification

### FR-CLS-01 — Multi-label classification (P0)

Каждый запрос получает одну или несколько бизнес-категорий с confidence. Taxonomy version сохраняется с результатом.

### FR-CLS-02 — `Other/Unknown` (P0)

Если ни одна категория не проходит утверждённый threshold или данных недостаточно, назначается `Other/Unknown`; система не выдумывает подходящую категорию.

### FR-CLS-03 — Explainability (P0)

Для назначения сохраняются краткая reason, релевантные masked fragments/features и версия метода. Reason не должна утверждать отсутствующий контекст.

### FR-CLS-04 — Начальная taxonomy (P0)

Конфигурируемая taxonomy может включать примеры ТЗ: генерация текста, помощь с кодом, анализ данных/таблиц/SQL, объяснение/обучение, поиск/сбор информации, планирование/управление задачами, нерабочие/общие вопросы и `Other/Unknown`. Конкретный состав утверждается как versioned configuration, а не hard-coded UI logic.

## 7. Use Case Discovery

### FR-CLU-01 — Clustering (P0)

Система группирует семантически похожие record embeddings, не требуя заранее полного списка сценариев. Записи вне устойчивых групп могут остаться noise.

### FR-CLU-02 — Cluster metrics (P0)

Для кластера сохраняются размер, доля, категории, quality/confidence и параметры алгоритма. Метрика качества не выдаётся за вероятность истинности.

### FR-CLU-03 — Representative samples (P0)

Для сценария выбираются разнообразные близкие к центру masked samples. Выбор детерминирован при фиксированном seed/configuration.

### FR-CLU-04 — Объяснение группировки (P0)

Система показывает общие семантические признаки и примеры, не раскрывая внутренние chain-of-thought модели.

## 8. Naming, Summarization и LLM

### FR-LLM-01 — Provider abstraction (P0)

Бизнес-логика обращается к интерфейсу LLM provider. Реализации: API provider (Gemini Flash через BotHub), mock provider и подключаемый local provider. H100 не требуется.

### FR-LLM-02 — Structured JSON (P0)

Ответы валидируются Pydantic-схемой. Невалидный JSON повторяется по ограниченной retry policy, затем переводится в fallback/failed без публикации свободного текста.

### FR-LLM-03 — Минимизация контекста (P0)

Провайдер получает только маскированные, сокращённые evidence snippets и агрегаты. Полный запрос среднего размера `100k токенов` не передаётся внешнему API.

### FR-LLM-04 — Batch, cache, retry (P0)

Запросы группируются в контролируемые batches, кешируются по provider/model/prompt/schema/evidence hash и повторяются только для retryable errors с backoff и jitter.

### FR-SUM-01 — Название и summary сценария (P0)

Сценарий получает краткое название, описание назначения, типовые формулировки и evidence references. Запрещены факты, отсутствующие в evidence.

## 9. Business Insights и Recommendations

### FR-INS-01 — Evidence-backed insights (P0)

Поддерживаются: top-сценарии, повторяющиеся ручные процессы, automation opportunities, возможности специализированных AI-агентов, prompt-quality issues и privacy risks.

### FR-INS-02 — Trends (P1, условно)

Растущие сценарии рассчитываются только при валидном timestamp и достаточном покрытии периодов. Иначе UI показывает `trend unavailable` с причиной.

### FR-REC-01 — Рекомендации CTO (P0)

Каждая рекомендация содержит действие, обоснование, связанные insights/scenarios, confidence и caveats. Radar не выполняет действие автоматически.

### FR-INS-03 — Эффективность (P0)

Система показывает usage/proxy signals по направлениям и командам при наличии полей. Реальная экономия и ROI не заявляются без outcome metrics.

## 10. AI Best Practices и Knowledge Discovery

### FR-BP-01 - Candidate Best Practice (P0)

После формирования Scenario система агрегирует разрешённые usage/outcome metadata и создаёт `BestPractice(status=detected)` только при прохождении versioned classifier. Повторный анализ одного scenario в tenant не создаёт дубликат.

### FR-BP-02 - Impact Score (P0)

Impact Score находится в диапазоне `0-100` и включает количество пользователей, частоту использования, пользовательскую оценку, экономию времени и успешность. Формула, weights, caps и версия classifier сохраняются и документируются.

### FR-BP-03 - Conservative detection (P0)

MVP требует одновременно высокий Impact Score, достаточное использование и число пользователей, высокую успешность, низкий error rate и положительную оценку. Отсутствующий outcome signal не считается положительным.

### FR-BP-04 - Recommendation (P0)

Каждая практика получает recommendation по распространению. Recommendation является предложением, не выполняет действие автоматически и содержит понятное основание.

### FR-BP-05 - Review workflow (P0)

Допустимые статусы: `detected`, `under_review`, `approved`, `rejected`, `published`. Publish разрешён только после approve. Совмещённый approve+publish допускается только в явно обозначенном demo-mode.

### FR-BP-06 - Comparable periods (P1)

Growth и FTE рассчитываются только для определённого observation period. Growth сравнивает окна одинаковой длительности; FTE нормализует экономию к месяцу или возвращает unavailable.

### FR-KD-01 - Knowledge Discovery (P0)

Dashboard показывает новые, быстрорастущие и наиболее эффективные практики, а также группировки по подразделениям и моделям. Отклонённые практики не входят в TOP.

### FR-KD-02 - Honest UI state (P0)

Demo fixtures разрешены только в demo environment. В api/production environment ошибка API отображается как error state и не маскируется демонстрационными практиками.

Полный контракт определён в [AI Best Practices и Knowledge Discovery](./23-best-practices.md).

## 11. Prompt Health

### FR-PH-01 — Checks (P0)

Система выявляет слишком короткие, чрезмерно длинные, неоднозначные, повторяющиеся, потенциально сломанные запросы и записи с sensitive/secret findings.

### FR-PH-02 — Конфигурируемые правила (P0)

Пороговые значения и версии правил сохраняются. Finding содержит rule id, severity, explanation и masked evidence.

## 12. Dashboard и Explainability

### FR-DSH-01 — Executive Overview (P0)

Показывает объём, validation quality, top categories, top use cases, insights, risks, recommendations и analysis status.

### FR-DSH-02 — Drill-down (P0)

Пользователь переходит overview → category/scenario → masked samples/explanation без потери фильтров dataset/run.

### FR-DSH-03 — States (P0)

Loading, empty, partial, degraded, failed и completed отображаются различимо и не заменяются фиктивными данными.

### FR-EXP-01 — Provenance (P0)

Для результата доступны source run, модель/алгоритм, версия конфигурации, время расчёта, confidence/quality и evidence references.

## 13. Report Generation

### FR-RPT-01 — PDF report (P0)

Пользователь генерирует PDF из сохранённого completed или degraded run. Отчёт включает executive summary, методологию, ограничения, категории, сценарии, insights, recommendations, prompt health и security overview.

### FR-RPT-02 — Consistency (P0)

Значения PDF совпадают с dashboard для того же run. Генерация не запускает анализ повторно.

## 14. Orchestration и операции

### FR-RUN-01 — Analysis run (P0)

Запуск создаёт immutable configuration snapshot и проходит конечный автомат состояний. Одновременный дублирующий запуск предотвращается idempotency key или явным подтверждением.

### FR-RUN-02 — Progress (P0)

UI получает текущий stage, counts и безопасное сообщение. Процент показывается только если знаменатель известен.

### FR-RUN-03 — Cancellation/restart (P1)

Пользователь может отменить активный run и создать новый; завершённые результаты не перезаписываются.

### FR-OPS-01 — Rate limiting (P0)

Upload, run creation, polling и report endpoints имеют конфигурируемые limits. Превышение возвращает `429` и `Retry-After`.

### FR-AUTH-01 — Authorization boundary (P0 architecture, P2 full UX)

Все dataset/run/report ресурсы связаны с tenant/owner context. В demo mode используется явный локальный principal; production authentication подключается без изменения domain logic.

## 15. Edge cases

- пустой файл, отсутствующий `text`, битая кодировка;
- одна валидная строка или все строки — дубликаты;
- один запрос длиннее model context;
- все классификации ниже threshold;
- clustering возвращает только noise или один кластер;
- timestamp отсутствует, неверен или покрывает один период;
- LLM timeout, `429`, invalid JSON или исчерпан retry budget;
- повторная загрузка идентичного файла;
- sensitive value находится в representative sample;
- PDF запрошен для незавершённого run.
- Best Practice не имеет rating/success metadata;
- detector повторно обрабатывает тот же source scenario;
- timestamp не позволяет построить два сопоставимых окна;
- rejected practice попадает в TOP;
- publish запрошен до approve;
- production API недоступен, а frontend работает не в demo-mode.

Во всех случаях система возвращает явный статус и не создаёт правдоподобный фиктивный результат.

## 16. Traceability

Требования реализуются только после детализации в [Dataset](./08-dataset.md), [Architecture](./09-architecture.md), [AI Pipeline](./10-ai-pipeline.md), [Backend](./12-backend.md), [Frontend](./13-frontend.md), [API](./15-api.md), [Security](./16-security.md) и [AI Best Practices](./23-best-practices.md).
