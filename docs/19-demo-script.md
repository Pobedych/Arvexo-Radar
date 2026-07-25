# Arvexo Radar: сценарий демонстрации

**Версия:** v0.1.0 — Hackathon MVP
**Аудитория:** жюри КРОК, CTO, AI Platform Owner

## 1. Цель демонстрации

Показать, как Arvexo Radar превращает журналы запросов в проверяемую аналитику и следующие действия, не скрывая качество данных, неопределённость и ограничения.

## 2. Подготовка

- запустить demo profile по README;
- использовать утверждённый reference/synthetic dataset без реальных секретов;
- заранее проверить модель/cache и mock fallback;
- не заявлять заранее рассчитанные цифры как универсальный benchmark;
- подготовить API mode и независимый mock mode;
- проверить PDF generation/download.

## 3. Сценарий

### Шаг 1. Открыть Arvexo Radar

**Показать:** product tagline и список datasets.
**Сообщение:** Radar — аналитический слой, а не AI-чат или средство оценки сотрудников.

### Шаг 2. Загрузить dataset

**Действие:** выбрать CSV.
**Показать:** ограничения формата, upload progress, server-created dataset.
**Сообщение:** файл считается недоверенным и не анализируется до validation.

### Шаг 3. Проверить Validation и Preview

**Показать:** mapping, accepted/rejected/warnings, masked preview, detection summary.
**Сообщение:** каждая строка учтена; sensitive values скрыты до следующих этапов.

### Шаг 4. Запустить анализ

**Показать:** immutable run configuration summary и provider mode.
**Сообщение:** local analytics не зависят от внешней генерации; H100 не используется.

### Шаг 5. Показать progress

**Показать:** реальные stages и counts.
**Сообщение:** запросы со средним размером 100k токенов обрабатываются chunks без silent truncation.

### Шаг 6. Открыть Executive Overview

**Показать:** объём, validation quality, top categories, top scenarios, top issues и next actions.
**Ответить:** «Что происходит с AI внутри организации?»

### Шаг 7. Исследовать категории

**Показать:** multi-label distribution, `Other/Unknown`, denominator note, confidence.
**Сообщение:** низкая уверенность не превращается в красивый выдуманный label.

### Шаг 8. Открыть use case

**Показать:** name, description, size/share, categories, quality, representative samples и grouping explanation.
**Сообщение:** похожие запросы группируются в конкретные сценарии внутри более широких категорий.

### Шаг 9. Проверить explainability

**Действие:** перейти от aggregate к masked evidence.
**Сообщение:** Radar показывает reason/provenance, но не раскрывает hidden chain-of-thought.

### Шаг 10. Открыть Insights и Recommendations

**Показать:** observation/hypothesis/recommendation, evidence links и caveats.
**Ответить:** «Что руководству делать дальше?»
**Ограничение:** usage proxy не называется доказанным ROI.

### Шаг 11. Открыть Prompt Health и Security

**Показать:** repeated/short/long/ambiguous/broken prompts, PII/secret findings и masked examples.
**Сообщение:** finding — сигнал для проверки, а не обвинение пользователя или доказанный incident.

### Шаг 12. Показать degradation

**Действие:** переключить подготовленный demo на mock/provider-unavailable fixture.
**Показать:** local results сохраняются, generated blocks маркированы degraded.
**Сообщение:** demo не рушится вместе с внешним API.

### Шаг 13. Сгенерировать PDF

**Показать:** report metadata и download; открыть титул, overview, scenarios, recommendations и limitations.
**Сообщение:** PDF использует тот же persisted run, что dashboard.

## 4. Контрольные вопросы после demo

1. Какие сценарии наиболее распространены?
2. Почему конкретные запросы объединены?
3. Где качество группировки/классификации низкое?
4. Какие проблемы относятся к prompt formulation/interface?
5. Какие действия подтверждены данными?
6. Какие выводы недоступны без timestamps/outcomes?

## 5. Запрещённые утверждения

- «Система гарантирует обнаружение всех секретов».
- «Этот сценарий точно сэкономит указанную сумму/время» без outcome data.
- «Модель имеет точность N%» без проведённой оценки.
- «Это production-ready enterprise deployment» для v0.1.0.
- «Данные КРОК показывают…», если используется synthetic/reference dataset.

## 6. План отказоустойчивой демонстрации

- основной path: API provider при доступности;
- fallback: cached valid structured responses;
- deterministic fallback: mock provider с явной меткой;
- сохранённый completed demo run допустим только с указанием, что это prepared result;
- отсутствие сети не должно блокировать local analytics/dashboard.

## 7. Acceptance criteria

- demo проходит последовательно без ручной правки DB;
- каждый тезис подтверждается видимым экраном/evidence;
- mock/API mode не маскируется;
- в UI/PDF нет реальных sensitive values;
- ограничения проговариваются до вопросов жюри.

## 8. Связанные документы

- [Dashboard](./11-dashboard.md)
- [Deployment](./17-deployment.md)
- [Judges FAQ](./20-judges-faq.md)

