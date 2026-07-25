# Radar Enterprise Effectiveness, TCO, ROI и Knowledge Adoption

## 1. Назначение

Radar объединяет три независимых контура: техническую наблюдаемость AI, расчёт бизнес-эффекта и распространение проверенных практик. Граница принципиальна: технически успешный ответ не считается качественным бизнес-результатом без outcome/benchmark.

## 2. Сущности migration 0005

| Сущность | Назначение |
|---|---|
| `llm_request_events` (расширение) | role, team, location, agent/scenario IDs, tool calls и request cost |
| `tool_usages` | фактический вызов инструмента, status/error/latency и связь с request |
| `cost_components` | effective-dated TCO, источник, allocation и флаг estimate |
| `methodology_settings` | FTE cost/hours, energy, depreciation, thresholds, currency/period |
| `scenario_benchmarks` | baseline/actual minutes, source/sample/confidence/approval |
| `practice_adoptions` | кому рекомендовано, статусы внедрения и эффект после adoption |
| `best_practices` (расширение) | origin, money saved, approval и recommended departments |

`model_tariffs` из migration 0004 остаётся effective-dated источником цен внешних моделей. Для внутренних моделей token tariff может быть нулевым: стоимость приходит через inference/infrastructure/hardware/electricity.

## 3. Системная телеметрия

Одна запись запроса содержит `request_id`, salted `user_id_hash`, role, department, team/location, agent/scenario, model, tool calls, UTC timestamps, status/error, latency/TTFT, tokens и request cost. Proxy принимает metadata в body/`X-Radar-*`, удаляет её перед upstream-вызовом и не сохраняет prompt/response content.

Агрегаты: total/success/failed, success/error rate, avg/median/p95 latency, TTFT, tokens, cost, DAU/WAU/MAU, unique users, requests/user и dimension breakdowns.

## 4. TCO: A

```text
A = Token Cost
  + Inference Cost
  + Infrastructure Cost
  + Hardware Depreciation
  + Electricity Cost
  + Subscription Cost
  + Support Cost
  + Other selected components
  + Development Team (только если включено в методике)
```

Allocation types:

- `requests` — пропорционально числу запросов;
- `tokens` — пропорционально total tokens;
- `inference_time` — пропорционально времени инференса;
- `fixed_share` — по долям, сумма которых равна 1;
- `agent` — 100% конкретному агенту.

Нулевая сумма веса считается ошибкой конфигурации. Отрицательные значения отклоняются. Распределение сохраняет исходную сумму точно; остаток Decimal относится последнему target.

## 5. Business Effect: B

```text
minutes_saved_per_task = baseline_minutes_without_ai - actual_minutes_with_ai
time_saved_minutes = Σ(completed_tasks × minutes_saved_per_task)
time_saved_hours = time_saved_minutes / 60
fte_saved = time_saved_minutes / monthly_work_minutes_per_fte
money_saved = fte_saved × average_monthly_fte_cost
net_benefit = money_saved - total_ai_cost
ROI = net_benefit / total_ai_cost × 100%
payback_ratio = money_saved / total_ai_cost
```

Для квартала/года FTE нормализуется как средний capacity equivalent, money saved остаётся итогом всего периода. При нулевой стоимости ROI и payback unavailable. Confidence ниже 50% даёт `insufficient_data`, даже если арифметическая оценка существует.

FTE Saved — эквивалент высвобождённого времени. Он не означает сокращение штата.

## 6. Scenario Benchmark

Источники: норматив, экспертная оценка, пользовательский опрос, A/B-замер, данные внутренней системы и ручной ввод. `source_type`, sample size, confidence, approval и `is_estimated` сопровождают результат до UI. Radar не утверждает причинно-следственную экономию без бизнес-бенчмарка.

## 7. Best Practice и Adoption

Rule-based v1 требует одновременно: высокий Impact, достаточную частоту, несколько пользователей, высокий success rate, низкий error rate, положительную rating, рост использования и подтверждённую экономию времени. Пороги хранятся в методике.

```text
detected → under_review → approved → published → scaling → archived
                    └──→ rejected
```

`recommend` создаёт/обновляет `Practice Adoption`. Adoption проходит `recommended → accepted → pilot → adopted`, либо `rejected/paused`. Отслеживаются active users, usages, time/money saved после внедрения и owner/comment. Prompt content не публикуется: карточка использует только обезличенное описание после экспертной проверки.

## 8. API

Analytics:

- `GET /api/analytics/overview`
- `GET /api/analytics/usage`
- `GET /api/analytics/models`
- `GET /api/analytics/agents`
- `GET /api/analytics/tools`
- `GET /api/analytics/departments`
- `GET /api/analytics/costs`
- `GET /api/analytics/business-effect`
- `GET /api/analytics/roi`
- `GET /api/analytics/insights`

Общие filters: `date_from`, `date_to`, `department`, `role`, `user`, `agent`, `model`, `scenario`, `tool`. Date interval полуоткрытый `[date_from, date_to)`.

Methodology/costs:

- `GET|PUT /api/methodology`
- `GET|POST /api/cost-components`
- `PUT|DELETE /api/cost-components/{id}`

Best Practice: list/top/detail, `review`, `approve`, `reject`, `publish`, `recommend`, adoption GET/POST.

## 9. Demo и источники production

Связный demo adapter находится в `backend/app/demo_enterprise.py`. Durable configuration/workflow seed запускается `python -m app.seed_demo`. В demo за июль 2026:

- 642 MAU, 28 400 запросов, 4 агента;
- A = 1 170 000 ₽;
- 907,67 часа, 5,673 FTE equivalent;
- B = 2 269 166,67 ₽;
- Net Benefit = 1 099 166,67 ₽, ROI ≈ 93,95%;
- есть profitable, loss-making и insufficient-data агенты;
- практики находятся в detected, approved и scaling, adoption — в recommended/accepted/pilot/adopted.

Production источники, которые нужно подключить:

1. AI gateway/agent SDK — requests, users, models, tools, tokens, status/latency.
2. HR/MDM — roles, departments, teams, location (без открытых ПДн в аналитике).
3. FinOps/ERP/asset inventory — subscriptions, infrastructure, GPU, electricity, support.
4. Business systems/time studies — completed tasks и benchmark duration.
5. Knowledge workflow/RBAC — reviewers, owners, adoption events и audit trail.

## 10. Ограничения MVP

- Enterprise API использует demo adapter при `ARVEXO_ENVIRONMENT=demo`; production adapters для HR/FinOps/outcome ещё не реализованы.
- Высокообъёмный request history — агрегированный synthetic fixture, а не 28 400 записей в БД.
- Методика и cost CRUD в demo хранятся в памяти процесса; PostgreSQL entities и idempotent seed готовы для persistent adapter.
- Tenant/auth остаются demo-mode; production требует IAM/RBAC и audit log.
- Валютная конвертация не выполняется: все dashboard monetary values должны приходить в RUB.

## 11. Проверка

```powershell
.\.venv\Scripts\python.exe -m pytest backend
.\.venv\Scripts\python.exe -m ruff check backend
cd frontend
npm run lint
npm run build
```

Тесты покрывают token prices, missing tariff, смену тарифа, allocations, time/FTE/money/net/ROI/B>A, zero division, negative/incomplete values, periods, agent/department aggregates, Candidate Best Practice, lifecycle и adoption.
