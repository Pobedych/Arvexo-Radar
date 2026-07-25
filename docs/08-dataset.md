# Arvexo Radar: спецификация dataset

**Версия:** v0.1.0 — Hackathon MVP
**Статус:** спецификация входных данных

## 1. Scope и источник требований

MVP анализирует batch dataset журналов пользовательских запросов к корпоративным AI-агентам. ТЗ КРОК указывает средний размер одного запроса `100k токенов` и приводит примеры задач из почты, CRM, Jira, Confluence, календарей, отчётности и проектного управления.

Примеры описывают содержание запросов, но не означают, что Radar подключается к этим системам.

## 2. Поддерживаемый формат MVP

- Формат: CSV с заголовком.
- Кодировка: UTF-8 или UTF-8 BOM.
- Разделитель: определяемый безопасным parser из ограниченного списка `,`, `;`, tab; неоднозначность требует выбора пользователя.
- Один файл на dataset; архивы и исполняемые файлы запрещены.
- Максимальный размер файла и строки задаётся конфигурацией развёртывания и показывается до upload. Значение не фиксируется без reference dataset и инфраструктурного бюджета.

## 3. Canonical schema

| Поле | Обязательное | Тип | Назначение |
|---|---:|---|---|
| `text` | Да | string | Текст пользовательского запроса |
| `request_id` | Нет | string | Стабильный внешний идентификатор |
| `timestamp` | Нет | ISO 8601 datetime | Время запроса для динамики |
| `user_id` | Нет | string | Псевдонимизированный автор для допустимых агрегатов |
| `team` | Нет | string | Команда для группировки эффективности/использования |
| `direction` | Нет | string | Бизнес-направление |
| `agent_id` | Нет | string | Идентификатор агента/платформы |
| `language` | Нет | BCP 47/string | Заявленный язык, подлежащий проверке |
| `metadata` | Нет | JSON string | Ограниченные дополнительные атрибуты |

Заголовки источника сопоставляются с canonical fields. Неизвестные поля по умолчанию не используются и не передаются LLM.

## 4. Идентификация записей

Если `request_id` отсутствует, система создаёт внутренний идентификатор из `dataset_id`, номера строки и случайного dataset salt. Hash текста не используется как публичный ID. Одинаковые тексты отмечаются как duplicates, но не удаляются автоматически: повторяемость может быть аналитическим сигналом.

## 5. Validation rules

| Код | Условие | Результат |
|---|---|---|
| `V001` | Файл пуст | Dataset rejected |
| `V002` | Нет заголовка или mapping для `text` | Dataset rejected |
| `V003` | Пустой/whitespace-only `text` | Row rejected |
| `V004` | Некорректная кодировка/CSV structure | Dataset или row rejected по локализуемости ошибки |
| `V005` | Невалидный timestamp | Row accepted без trend eligibility и с warning |
| `V006` | Duplicate `request_id` с разным содержимым | Conflict; анализ блокируется до разрешения |
| `V007` | Длина превышает configured hard limit | Row rejected с безопасной причиной |
| `V008` | Неизвестные поля | Ignored с warning |
| `V009` | Нет валидных rows | Analysis disabled |

Каждая строка получает `accepted`, `accepted_with_warnings` или `rejected`. Counts должны сходиться с количеством data rows.

## 6. Normalization

Допустимо:

- привести Unicode к NFC;
- нормализовать CRLF/LF;
- удалить NUL и явно запрещённые control characters;
- ограниченно нормализовать внешний whitespace;
- привести timestamp к UTC при наличии offset.

Недопустимо молча исправлять смысл, переводить текст, удалять части длинного запроса или объединять записи.

## 7. Sensitive data masking

До embeddings и дальнейшей аналитики выполняется выявление email, phone, API keys и secret patterns. Замена использует placeholders вида `[EMAIL_1]`, `[PHONE_1]`, `[SECRET_1]` внутри записи. Mapping не передаётся внешнему LLM и не возвращается через API MVP.

`user_id`, `team` и `direction` считаются потенциально чувствительными metadata; доступ и агрегация определяются tenant policy. Малые группы не должны показываться без согласованного suppression threshold, который задаётся конфигурацией.

## 8. Обработка среднего запроса 100k токенов

`100k токенов` принимается как среднее значение из ТЗ, а не как максимум. Следствия:

1. длина измеряется tokenizer, соответствующим модели, и в символах для защитного pre-check;
2. запись разбивается на chunks с overlap и сохраняемой позицией;
3. chunks маскируются до model processing;
4. record representation агрегируется из chunk-level результатов;
5. representative samples выбираются как короткие masked excerpts;
6. во внешний LLM передаются только отобранные excerpts и агрегаты;
7. полное молчаливое truncation запрещено;
8. hard limits остаются конфигурируемыми для защиты ресурсов.

Конкретные token/chunk limits зависят от выбранной локальной модели и фиксируются в [AI Pipeline](./10-ai-pipeline.md) как versioned configuration.

## 9. Временные данные и trends

Trend analysis разрешён, только если:

- `timestamp` успешно разобран для достаточной доли записей;
- присутствуют минимум два сопоставимых периода;
- timezone и granularity задокументированы;
- UI показывает размер основания каждого периода.

Числовой порог достаточности утверждается после изучения фактического dataset. При невыполнении условий результат — `trend_unavailable`, а не нулевая динамика.

## 10. Пример входа

```csv
request_id,timestamp,team,direction,agent_id,text
r-001,2026-07-01T09:15:00+03:00,Sales,Commercial,assistant,"Подготовь краткую сводку писем за день по заданным критериям"
r-002,2026-07-01T10:00:00+03:00,Delivery,Operations,assistant,"Покажи мои задачи в Jira по приоритету"
```

Пример синтетический и не является записью КРОК.

## 11. Канонический результат строки

```json
{
  "record_id": "internal-id",
  "status": "accepted_with_warnings",
  "normalized_text_ref": "protected-storage-reference",
  "masked_text": "Напиши ответ для [EMAIL_1]",
  "token_count": 8,
  "warnings": ["sensitive_data_masked"],
  "trend_eligible": true
}
```

API не обязан возвращать `normalized_text_ref`; это обозначение внутреннего разделения данных.

## 12. CSV Injection и экспорт

CSV parser не вычисляет формулы. При будущем CSV/Excel-compatible export любое значение с опасным начальным символом экранируется. PDF и HTML также выполняют output escaping. Наличие Excel-задач внутри текста не превращает их в команды.

## 13. Data lifecycle MVP

- Upload создаёт dataset и checksum.
- Validation/normalization/masking создают immutable processing version.
- Analysis run ссылается на конкретную processing version.
- Повторная загрузка совпадающего checksum не перезаписывает существующий dataset.
- Retention и удаление конфигурируются; автоматический срок не выдумывается до security/privacy решения.

## 14. Открытые параметры реализации

До начала реализации должны быть выбраны на reference dataset:

- file/row hard limits;
- chunk size и overlap;
- поддерживаемые языки локальных моделей;
- suppression threshold для малых групп;
- допустимая доля timestamp для trends;
- retention period.

Эти параметры не меняют продуктовый scope и должны храниться версионированно.

## 15. Критерии приёмки

- **DATA-AC-01:** каждая data row учтена в accepted/warning/rejected counts.
- **DATA-AC-02:** анализ не использует unmasked text после masking boundary.
- **DATA-AC-03:** 100k-token record обрабатывается chunked strategy без silent truncation.
- **DATA-AC-04:** отсутствие времени отключает trends с объяснением.
- **DATA-AC-05:** unknown columns не передаются внешним провайдерам.
- **DATA-AC-06:** примеры ТЗ используются как темы, а не как доказанный production dataset.

## 16. Связанные документы

- [Functional Requirements](./07-functional-requirements.md)
- [AI Pipeline](./10-ai-pipeline.md)
- [Database](./14-database.md)
- [Security](./16-security.md)
