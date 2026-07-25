# Arvexo Radar: dashboard

**Версия:** v0.1.0 — Hackathon MVP
**Статус:** UX и information architecture specification

## 1. Цель

Dashboard позволяет CTO за несколько минут понять «что происходит?» и «что делать дальше?», а AI Platform Owner — проверить данные и объяснения.

## 2. Навигация MVP

1. Datasets
2. Upload & Validation
3. Analysis Progress
4. Executive Overview
5. Categories
6. Use Cases
7. Business Insights & Recommendations
8. Prompt Health & Security
9. Report
10. AI Best Practices
11. Knowledge Discovery

## 3. Executive Overview

Первый экран completed run содержит:

- dataset/run identity и status badge;
- processed, rejected и warning counts;
- top categories и top use cases;
- usage breakdown по direction/team, если доступен;
- trend cards только при валидном времени;
- top prompt-health/security issues;
- evidence-backed insights;
- recommended next actions;
- явные limitations/degraded notices.

Не допускаются vanity metrics без определения и знаменателя.

## 4. Экран Upload & Validation

- drop zone и поддерживаемые ограничения;
- column mapping;
- masked preview;
- accepted/rejected/warning summary;
- причины по validation code;
- подтверждение запуска только для валидных данных.

Raw sensitive values не отображаются даже до анализа.

## 5. Analysis Progress

Показываются stage, completed/total units при известном total, elapsed time, safe status message и cancellation (P1). Fake linear progress запрещён. Polling использует TanStack Query с backoff и останавливается в terminal state.

## 6. Categories

- bar/donut chart с доступной таблицей;
- count, share, confidence distribution;
- multi-label denominator explanation;
- `Other/Unknown` отображается явно;
- filter → masked requests и classification reasons.

При multi-label сумма долей может превышать 100%; UI обязан это объяснять.

## 7. Use Cases

Список/таблица сценариев: name, description, size, share, categories, quality, trend status. Detail drawer/page содержит typical phrasings, diverse representative samples, grouping explanation, evidence count и caveats.

Noise не скрывается и не получает сгенерированное название.

## 8. Insights и Recommendations

Карточка insight маркируется `Observation` или `Hypothesis`, содержит evidence count и ссылки. Recommendation содержит action, rationale, priority basis и caveats. UI не использует imperative «сделать обязательно» при низкой confidence.

## 9. AI Best Practices

Карточка практики содержит title, description, department, users, time saved, FTE saved, Impact Score, status, recommendation и действие распространения. Полный каталог поддерживает поиск и фильтр по status.

На Executive Overview показываются ведущие практики без дублирования полного каталога. Действие «Рекомендовать другим подразделениям» публикует `approved` practice; review и publish не объединяются в production UX.

## 10. Knowledge Discovery

Экран содержит TOP новых, быстрорастущих и наиболее эффективных практик, группировки по подразделениям и моделям. Growth отображается только при валидных сопоставимых периодах; unavailable не показывается как нулевой рост. `rejected` исключается из подборок.

## 11. Prompt Health & Security

Показываются counts/rates по rule, severity, динамика при доступности и masked examples. Секретное значение никогда не показывается; security finding — потенциальный сигнал, не доказанный incident.

## 12. Filters

Допустимые фильтры: category, scenario, direction, team, agent, time range, finding type, Best Practice status, department, model и minimum Impact Score - только если поле доступно. Активные filters видимы, сериализуемы в URL и сбрасываются явно. Малые группы могут подавляться security policy.

## 13. UI states

| State | Представление |
|---|---|
| Loading | Skeleton с сохранением layout |
| Empty | Причина и следующее действие |
| Partial | Доступные результаты + отсутствующие блоки |
| Degraded | Warning banner + provider/stage impact |
| Failed | Error code, безопасное описание, retry action |
| Completed | Полные доступные результаты |

Demo practices разрешены только при явном demo environment. Ошибка production API отображается как Error и не подменяется demo fixtures.

## 14. Визуализация

Recharts используется для количественных сравнений. Таблица сопровождает chart там, где нужны точные значения. Цвет не является единственным носителем смысла; легенды, labels и tooltips доступны с клавиатуры. 3D charts, gauges без шкалы и декоративная анимация не используются.

## 15. Responsive и accessibility

- desktop-first для executive use, usable от tablet width;
- keyboard navigation и visible focus;
- semantic headings/tables;
- WCAG AA contrast target;
- reduced-motion preference;
- locale-ready formatting чисел и дат.

## 16. PDF entry point

Report screen показывает run, состав отчёта, generated/degraded status и download. Генерация запрещена до terminal analytics state. PDF включает те же metrics и limitations.

## 17. Acceptance criteria

- **UI-AC-01:** top findings видны без просмотра raw rows.
- **UI-AC-02:** любой insight раскрывается до evidence.
- **UI-AC-03:** unavailable trend не выглядит как zero.
- **UI-AC-04:** multi-label shares объяснены.
- **UI-AC-05:** provider degradation видна.
- **UI-AC-06:** sensitive value не появляется в UI.
- **UI-AC-07:** Best Practice card содержит все обязательные поля и recommendation.
- **UI-AC-08:** Knowledge Discovery показывает пять обязательных срезов.
- **UI-AC-09:** production API failure не выглядит как успешный demo response.
- **UI-AC-10:** publish не обходит review workflow.

## 18. Связанные документы

- [Personas](./04-personas.md)
- [Frontend](./13-frontend.md)
- [API](./15-api.md)
- [AI Best Practices](./23-best-practices.md)
