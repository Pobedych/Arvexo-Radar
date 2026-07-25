# Arvexo Radar: frontend

**Версия:** v0.1.0 — Hackathon MVP
**Стек:** Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Recharts, TanStack Query

## 1. Архитектура frontend

```text
frontend/
  app/                 # routes, layouts, error/loading boundaries
  components/
    ui/                # shadcn primitives
    charts/
    datasets/
    analysis/
    explainability/
  features/            # feature-level composition
  lib/api/             # typed HTTP client
  lib/query/           # keys and query options
  types/               # generated/shared API types
  tests/
```

## 2. Rendering и state

- Server Components используются для shell и безопасных initial reads, где это уместно.
- Client Components ограничены upload, filters, charts и polling interactions.
- TanStack Query владеет server state; локальный React state не дублирует API cache.
- URL содержит dataset/run/filter context.
- API key и backend secrets не попадают в browser bundle.

## 3. Routes

- `/datasets`
- `/datasets/new`
- `/datasets/[datasetId]/validation`
- `/datasets/[datasetId]/runs/[runId]/progress`
- `/datasets/[datasetId]/runs/[runId]/overview`
- `/datasets/[datasetId]/runs/[runId]/categories`
- `/datasets/[datasetId]/runs/[runId]/scenarios`
- `/datasets/[datasetId]/runs/[runId]/prompt-health`
- `/datasets/[datasetId]/runs/[runId]/report`

## 4. Typed API

HTTP client обрабатывает единую error schema, correlation ID, cancellation и `429 Retry-After`. TypeScript types должны генерироваться или проверяться против OpenAPI; ручное расхождение типов не допускается.

## 5. Query policy

- стабильные hierarchical query keys;
- terminal run results считаются immutable;
- progress polling использует adaptive interval;
- retries отключены для validation/authorization errors;
- mutation success инвалидирует только связанные keys;
- stale previous run data не показывается как результат нового run.

## 6. Upload UX

Client-side checks улучшают обратную связь, но server validation остаётся authoritative. Upload progress показывает фактически переданные bytes. Preview получает уже masked values с API.

## 7. Charts и tables

Recharts получает готовые агрегаты API и не пересчитывает business metrics. Каждая chart имеет title, definition, denominator, accessible table/summary и empty/degraded state. Цветовые mappings категорий стабильны в рамках run.

## 8. Explainability UI

Reason, confidence/quality, evidence count, masked excerpts, model/config provenance и caveats представлены отдельными полями. Нельзя показывать скрытые reasoning traces или имитировать точность чрезмерным количеством знаков.

## 9. Error handling

Route error boundary показывает safe message, correlation ID и релевантное действие. Ошибки section-level не обрушивают весь overview. Никогда не рендерится необработанный HTML из dataset/LLM.

## 10. Security

- no `dangerouslySetInnerHTML` для данных/LLM output;
- output escaped React defaults;
- downloads только по API-authorized URL/response;
- auth/session mechanism выбирается архитектурой, не localStorage token по умолчанию;
- CSP и security headers задаются deployment/frontend config;
- client filename не используется как path.

## 11. Accessibility и quality

- semantic landmark/navigation;
- keyboard operability;
- visible focus и reduced motion;
- labels для inputs/charts;
- responsive desktop/tablet layout;
- component, integration и critical e2e tests.

## 12. Acceptance criteria

- **FE-AC-01:** все server states различимы.
- **FE-AC-02:** filters воспроизводимы через URL.
- **FE-AC-03:** charts и PDF не считают разные metrics.
- **FE-AC-04:** raw/unsafe HTML не рендерится.
- **FE-AC-05:** UI не содержит provider secret.
- **FE-AC-06:** основной demo flow доступен с клавиатуры.

## 13. Связанные документы

- [Dashboard](./11-dashboard.md)
- [API](./15-api.md)
- [Security](./16-security.md)

