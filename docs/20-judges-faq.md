# Arvexo Radar: FAQ для жюри

**Версия:** v0.1.0 — Hackathon MVP

## 1. Что решает Arvexo Radar?

Он преобразует журналы запросов к корпоративным AI-агентам в категории, обнаруженные use cases, prompt-health/security signals, бизнес-инсайты и проверяемые рекомендации для CTO и AI Platform Owner.

## 2. Чем категория отличается от use case?

Категория — широкая бизнес-тема, например «помощь с кодом». Use case — устойчивый семантический сценарий внутри или на пересечении категорий, например «объяснение Python traceback». Запрос может иметь несколько категорий; сценарии обнаруживаются clustering.

## 3. Как проверяется качество группировки?

Сочетаются cluster diagnostics, representative samples и экспертная проверка принципа «похожие вместе, разные разделены». До размеченного reference dataset мы не публикуем фиктивный процент точности.

## 4. Почему не использовать только LLM?

Полный массив длинных запросов дороже, менее воспроизводим и рискован для конфиденциальности. Local embeddings/classification/clustering создают доказательную структуру; LLM получает только masked evidence для названий, summaries и рекомендаций.

## 5. Как обрабатываются запросы по 100k токенов?

Это средний размер из ТЗ. Запрос маскируется и разбивается на bounded chunks; chunk representations агрегируются на уровень записи. Silent truncation и передача полного текста внешнему provider запрещены.

## 6. Используется ли H100?

Нет, в v0.1.0 H100 не используется. Генеративный слой работает через BotHub/Gemini Flash API, а provider abstraction поддерживает mock и подключаемый local provider для тестов.

## 7. Что произойдёт без API key или сети?

Local analytics продолжит работать. Mock mode не требует ключа. При отказе API run становится `degraded`, но категории, кластеры, metrics и доступные cached/fallback тексты сохраняются с явной меткой.

## 8. Как предотвращаются галлюцинации?

LLM получает ограниченный evidence package и возвращает JSON по строгой schema. Каждый insight/recommendation связан с evidence; invalid output повторяется ограниченно и затем отклоняется/fallback. Низкая уверенность отображается явно.

## 9. Как защищаются данные?

Файл проходит validation, запросы — masking email/phone/API-key/secret patterns до embeddings/LLM. Raw values не попадают в logs, UI, PDF или внешний payload. Доступ tenant-scoped; uploads и API rate-limited.

## 10. Гарантирует ли masking отсутствие утечек?

Нет. Detectors снижают риск, но могут ошибаться. Поэтому применяются одновременно minimization, restricted access, safe logs, tests с canaries и отказ от передачи лишнего контекста.

## 11. Может ли Radar измерить эффективность внедрения AI?

Он показывает подтверждённые логами usage/proxy signals по направлениям и командам при наличии полей: распространённость, рост, проблемы и automation potential. Экономия времени, качество результата и ROI требуют outcome data и не выдумываются.

## 12. Почему trends могут отсутствовать?

Тренд корректен только при валидных timestamps и сопоставимых периодах. Без них Radar показывает `trend unavailable`, а не нулевой рост.

## 13. Как выбираются representative samples?

Локально и воспроизводимо: близость к центру кластера, разнообразие и исключение дубликатов. Показываются короткие masked excerpts и reason выбора.

## 14. Можно ли оценивать сотрудников?

Нет. Radar предназначен для организационной аналитики использования AI. Даже если входной запрос описывает управление сотрудниками, продукт не строит персональные рейтинги авторов или объектов запроса.

## 15. Что делает решение продуктом, а не notebook?

Есть безопасный upload, validation/preview, управляемый pipeline, progress, persisted runs, executive dashboard, explainability, graceful degradation, API, PDF и воспроизводимый Docker flow.

## 16. Почему выбран этот стек?

Он зафиксирован владельцем продукта: Next.js/TypeScript для web, FastAPI/Python для data/ML, PostgreSQL/pgvector для transactional state и vectors, Docker Compose для воспроизводимого MVP. Новые инфраструктурные сервисы не добавлены без необходимости.

## 17. Какие ограничения MVP наиболее важны?

Не утверждены production SSO/retention/SLA, точная модель выбирается после dataset audit, connectors и streaming отсутствуют, а эффективность ограничена proxy signals без outcomes.

## 18. Как воспроизвести результат?

Run хранит dataset version/checksum, taxonomy, model/prompt/chunking versions, algorithm parameters, seed и provider provenance. Генеративная недетерминированность явно отделена и кешируется по evidence/config hash.

## 19. Что будет развиваться после MVP?

Только после отдельного решения: production IAM, connectors, feedback/annotation, outcomes/ROI, object storage/observability и incremental processing. Они не выдаются за уже реализованный scope.

## 20. Где полная спецификация?

В каталоге `docs/`; навигация приведена в корневом `README.md`. [Vision](./01-vision.md), [Functional Requirements](./07-functional-requirements.md), [Architecture](./09-architecture.md), [Security](./16-security.md).

