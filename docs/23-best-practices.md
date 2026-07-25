# Arvexo Radar: AI Best Practices и Knowledge Discovery

**Версия:** v0.2.0 - MVP
**Статус:** актуализированная функционально-техническая спецификация
**Дата ревью:** 25 июля 2026

## 1. Цель

Radar должен не только измерять использование ИИ, но и находить доказанные повторяемые способы работы, сохранять их как управляемые Best Practices и помогать переносить их между подразделениями.

Модуль не оценивает отдельных сотрудников. Все выводы строятся на агрегированных сценариях и безопасных metadata signals.

## 2. Термины

- **Scenario** - кластер похожих AI-запросов, найденный analysis pipeline.
- **Candidate Best Practice** - сценарий, прошедший правила обнаружения; в БД это `BestPractice` со статусом `detected`.
- **Published Best Practice** - согласованная практика, доступная для распространения.
- **Observation period** - период данных, для которого рассчитаны usage, growth, time saved и FTE.

## 3. Сущность Best Practice

Обязательные поля исходного ТЗ:

- `id`;
- `title`;
- `short_description`;
- `department`;
- `scenario`;
- `created_at`;
- `detected_at`;
- `status`;
- `confidence_score`;
- `impact_score`;
- `adoption_count`;
- `estimated_time_saved`;
- `estimated_fte_saved`;
- `tags`.

Дополнительные поля, появившиеся при реализации:

- `tenant_id` - security boundary;
- `source_scenario_id` - связь с исходным сценарием;
- `recommendation` - рекомендация по распространению;
- `user_count`, `usage_count`, `average_rating`, `success_rate`, `error_rate`, `growth_rate` - объяснимые агрегаты;
- `departments`, `models` - многозначные группировки Knowledge Discovery;
- `detection_evidence` - версия classifier и сработавшие правила;
- `published_at` - время публикации.

Unique constraint `(tenant_id, source_scenario_id)` делает detection идемпотентным и не позволяет создать дубликат кандидата из одного сценария.

## 4. Статусы и переходы

Допустимые статусы:

```text
detected -> under_review -> approved -> published
                      \-> rejected
```

Правила:

- `approve` разрешён для `detected` и `under_review`;
- `publish` разрешён только для `approved`;
- повторный approve для `approved/published` и повторный publish для `published` идемпотентны;
- `rejected` не попадает в публичные TOP-подборки;
- UI не должен автоматически согласовывать практику от имени пользователя без явно разрешённого demo-mode или отдельного permission.

Кнопка «Рекомендовать другим подразделениям» публикует уже согласованную практику. Для `detected/under_review` UI сначала показывает отдельное действие согласования. Совмещённый approve+publish допускается только в demo-mode и должен быть явно обозначен.

## 5. Входные сигналы

Detector использует только агрегаты Scenario и разрешённые поля Record metadata:

- canonical: `user_id`, `team`, `direction`, `agent_id`, `timestamp`;
- JSON metadata allowlist: `department`, `model`, `rating`, `time_saved_minutes`, `success`, `error`;
- Scenario: `name`, `description`, `category_ids`, `quality.cohesion`, members.

Неизвестные JSON metadata keys не сохраняются в аналитическом payload. Отсутствующие rating/success/time signals не считаются положительным результатом.

## 6. Impact Score

Impact Score принимает значение `0-100`:

```text
user_score      = clamp(user_count / 20)
frequency_score = clamp(usage_count / 50)
rating_score    = clamp((average_rating - 1) / 4)
time_score      = clamp(time_saved_hours / 40)
success_score   = clamp(success_rate)

Impact Score = 100 * (
    0.20 * user_score
  + 0.20 * frequency_score
  + 0.20 * rating_score
  + 0.20 * time_score
  + 0.20 * success_score
)
```

Все caps и weights являются versioned configuration classifier `rule-based-v1`; изменение требует новой версии classifier и сохранения версии в `detection_evidence`.

Если `average_rating` отсутствует, компонент Impact Score получает нейтральное значение `0.5`, но правило `positive_rating` не проходит и Candidate не создаётся.

## 7. Правила обнаружения MVP

Candidate создаётся только при одновременном выполнении условий:

- Impact Score `>= 70`;
- usage count `>= 8`;
- distinct user count `>= 3`;
- success rate `>= 0.80`;
- error rate `<= 0.20`;
- average rating `>= 4.0`.

Growth, multi-department spread и модели сохраняются как discovery signals. В `rule-based-v1` они не являются самостоятельными альтернативными trigger conditions.

## 8. Confidence Score

Confidence Score отражает качество evidence, а не бизнес-эффект:

- 55% - полнота department/model/user/rating/time/usage signals;
- 30% - cohesion исходного Scenario;
- 15% - объём наблюдений с насыщением на 30 использованиях.

Значение ограничивается диапазоном `0-100`. UI обязан отличать Confidence Score от Impact Score.

## 9. Growth и периоды

Growth рассчитывается только при наличии timestamp и двух сопоставимых окон одинаковой длительности:

```text
growth_rate = (current_period_usage - previous_period_usage)
              / max(previous_period_usage, 1)
```

Границы периодов, timezone, количество наблюдений и причина unavailable сохраняются в `detection_evidence`. Деление отсортированных записей пополам без временных границ не соответствует ТЗ.

`estimated_time_saved` хранится в часах за observation period. `estimated_fte_saved` для месячного периода рассчитывается как `monthly_time_saved_hours / 160`. Для другого периода часы сначала нормализуются к месяцу; период и формула сохраняются в evidence. При отсутствии периода FTE маркируется unavailable, а не вычисляется как месячный.

## 10. Recommendations

Каждая практика содержит recommendation. Rule-based MVP поддерживает:

- один юридический/договорный сценарий - рекомендация отделу закупок;
- отчётность/данные - рекомендация финансовому блоку;
- практика уже используется в нескольких подразделениях - масштабирование;
- общий high-impact сценарий - масштабирование.

Recommendation является предложением и не запускает автоматизацию или организационное изменение.

## 11. API

Обязательные endpoints:

- `GET /api/best-practices`;
- `GET /api/best-practices/top`;
- `GET /api/best-practices/{id}`;
- `POST /api/best-practices/{id}/approve`;
- `POST /api/best-practices/{id}/publish`.

Расширения list API: `status`, `department`, `model`, `min_impact_score`, `offset`, `limit`.

`GET /top` возвращает:

- `new` - по `detected_at`;
- `fast_growing` - по валидному `growth_rate`;
- `most_effective` - по `impact_score`;
- `by_department`;
- `by_model`.

TOP-подборки по умолчанию исключают `rejected`. Все lookup и mutation tenant-scoped. Production authentication не заменяется demo tenant.

## 12. Dashboard

Интерфейс реализуется внутри предоставленного Arvexo Dashboard и сохраняет его shell, палитру, навигацию и responsive behavior.

Раздел `AI Best Practices` содержит:

- название и описание;
- подразделение;
- количество пользователей;
- экономию времени;
- экономию FTE;
- Impact Score;
- статус;
- recommendation;
- кнопку «Рекомендовать другим подразделениям».

Экран `Knowledge Discovery` содержит:

- ТОП новых практик;
- ТОП быстрорастущих практик;
- самые эффективные сценарии;
- практики по подразделениям;
- практики по моделям.

Loading, empty, error и completed различимы. Demo fixtures разрешены только при явном demo environment. В api/production environment сетевой или server error показывается как error state и не подменяется успешными демонстрационными данными.

## 13. Расширяемость

`BestPracticeClassifier` является port/protocol:

```text
evaluate(PracticeSignals) -> DetectionDecision
```

`RuleBasedBestPracticeClassifier` - текущая реализация. Будущий AI classifier обязан возвращать тот же typed result, версию модели, confidence и explainable evidence без изменения public API и таблицы Best Practice.

## 14. Acceptance criteria

- **BP-AC-01:** миграция создаёт все обязательные и evidence-поля.
- **BP-AC-02:** Impact Score детерминирован, ограничен `0-100` и покрыт unit tests.
- **BP-AC-03:** отсутствие rating/success не создаёт ложный Candidate.
- **BP-AC-04:** повторный detector run не создаёт дубликат scenario candidate.
- **BP-AC-05:** approve/publish соблюдают state machine и tenant boundary.
- **BP-AC-06:** rejected не попадает в TOP.
- **BP-AC-07:** growth использует сопоставимые временные окна или unavailable.
- **BP-AC-08:** FTE учитывает observation period или unavailable.
- **BP-AC-09:** production API error не подменяется demo fixtures.
- **BP-AC-10:** Dashboard и Knowledge Discovery доступны с клавиатуры и на ширине 390 px.
- **BP-AC-11:** classifier заменяется через protocol без изменения router/DB contracts.
- **BP-AC-12:** repository/API integration tests проверяют tenant scope, filters и transitions.

## 15. Результат ревью реализации

| Область | Статус | Комментарий |
|---|---|---|
| Схема БД и статусы | Выполнено | Обязательные и дополнительные evidence-поля присутствуют |
| Impact Score | Выполнено | Формула и thresholds покрыты unit tests |
| Rule-based detector | Выполнено частично | Основные gates работают; growth требует исправления окон |
| Recommendations | Выполнено | Rule-based тексты формируются автоматически |
| API lifecycle | Выполнено частично | Все пять endpoints есть; tenant пока жёстко задан demo-константой |
| TOP и группировки | Выполнено частично | Требуется исключить rejected и валидировать growth |
| Dashboard cards | Выполнено | Все поля и действие присутствуют |
| Knowledge Discovery | Выполнено | Все пять представлений присутствуют |
| UI states | Выполнено частично | Production error сейчас маскируется demo fallback |
| Review workflow | Выполнено частично | UI объединяет approve и publish одним действием |
| Автотесты | Выполнено частично | Unit/OpenAPI есть; repository/API integration tests отсутствуют |

## 16. Связанные документы

- [Functional Requirements](./07-functional-requirements.md)
- [Architecture](./09-architecture.md)
- [Dashboard](./11-dashboard.md)
- [Backend](./12-backend.md)
- [Frontend](./13-frontend.md)
- [Database](./14-database.md)
- [API](./15-api.md)
