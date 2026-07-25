# Arvexo Radar: API

**Версия:** v1 API для Arvexo Radar v0.1.0
**Base path:** `/api/v1`
**Формат:** JSON, кроме multipart upload и PDF download

## 1. Общие соглашения

- UUID identifiers;
- ISO 8601 UTC timestamps;
- pagination: `cursor`, `limit`;
- idempotent creates принимают `Idempotency-Key`;
- correlation ID возвращается в `X-Correlation-ID`;
- unknown request fields rejected для critical commands;
- OpenAPI генерируется FastAPI и является machine-readable contract.

## 2. Error schema

```json
{
  "error": {
    "code": "DATASET_INVALID",
    "message": "Dataset does not contain a mapped text column.",
    "retryable": false,
    "details": {"field": "text"},
    "correlation_id": "uuid"
  }
}
```

`details` не содержит request text, secret, filesystem path или provider payload.

## 3. Endpoints

### System

- `GET /health` — process liveness, без dependency details.
- `GET /ready` — DB/storage/model readiness с безопасными codes.

### Datasets

- `POST /datasets` — multipart CSV upload; создаёт dataset/validation job; `201`.
- `GET /datasets` — список доступных principal datasets.
- `GET /datasets/{dataset_id}` — metadata/status.
- `GET /datasets/{dataset_id}/validation` — summary, mapping и safe row errors.
- `GET /datasets/{dataset_id}/preview` — paginated masked preview.
- `PATCH /datasets/{dataset_id}/mapping` — mapping до immutable processed version.

### Analysis runs

- `POST /datasets/{dataset_id}/runs` — создаёт run из validated version; `202`.
- `GET /runs/{run_id}` — status, stage, progress, degradation.
- `POST /runs/{run_id}/cancel` — P1 cancellation.
- `GET /runs/{run_id}/overview` — executive aggregates.
- `GET /runs/{run_id}/categories` — category distribution.
- `GET /runs/{run_id}/categories/{category_id}` — detail/explanations.
- `GET /runs/{run_id}/scenarios` — scenario list.
- `GET /runs/{run_id}/scenarios/{scenario_id}` — summary, members/samples.
- `GET /runs/{run_id}/insights` — typed insights/recommendations.
- `GET /runs/{run_id}/prompt-health` — rule aggregates/findings.
- `GET /runs/{run_id}/security-findings` — safe aggregated findings.

### Reports

- `POST /runs/{run_id}/reports` — create PDF job from terminal run; `202`.
- `GET /reports/{report_id}` — status/metadata.
- `GET /reports/{report_id}/download` — authorized PDF stream.

## 4. Example: create run

```http
POST /api/v1/datasets/7e.../runs
Idempotency-Key: demo-run-001
Content-Type: application/json

{
  "provider_mode": "mock",
  "taxonomy_version": "v1",
  "locale": "ru-RU"
}
```

Ответ:

```json
{
  "run_id": "8a...",
  "status": "queued",
  "stage": null,
  "links": {"self": "/api/v1/runs/8a..."}
}
```

Client не передаёт model names, thresholds или secrets произвольно; разрешённая server configuration snapshot создаётся backend.

## 5. Run response

```json
{
  "run_id": "8a...",
  "dataset_id": "7e...",
  "status": "degraded",
  "stage": "completed",
  "progress": {"completed": 1000, "total": 1000, "unit": "records"},
  "degradations": [
    {"code": "LLM_PROVIDER_UNAVAILABLE", "affected": ["scenario_wording"]}
  ],
  "provenance": {"config_version": "sha256:..."}
}
```

## 6. Overview response rules

Response возвращает `denominator`, `availability` и `limitations` рядом с metrics. Multi-label category shares маркируются `overlapping=true`. Trend block имеет `available=false` и reason, а не пустой series.

## 7. Authorization

Каждый resource lookup ограничен tenant/principal context до возврата существования ресурса. IDOR предотвращается repository-level scope. Demo mode principal явный и не должен автоматически включаться в production config.

## 8. Rate limits и status codes

- `400` malformed input;
- `401/403` authentication/authorization;
- `404` resource not visible/existing;
- `409` invalid state/idempotency conflict;
- `413` file too large;
- `415` unsupported media type;
- `422` semantic validation;
- `429` rate limit + `Retry-After`;
- `500` unexpected safe error;
- `503` dependency unavailable/readiness.

Конкретные limits конфигурируются deployment profile.

## 9. Versioning

Breaking contract change создаёт `/api/v2` или согласованный migration window. Добавление optional response fields допустимо; frontend не должен падать на неизвестных полях. Provider schema versions независимы от public API version.

## 10. Acceptance criteria

- **API-AC-01:** OpenAPI соответствует Pydantic schemas.
- **API-AC-02:** все resource endpoints tenant-scoped.
- **API-AC-03:** create run/report idempotent.
- **API-AC-04:** errors не раскрывают sensitive data.
- **API-AC-05:** partial/degraded отличается от empty/success.
- **API-AC-06:** PDF доступен только для authorized principal.

## 11. Связанные документы

- [Backend](./12-backend.md)
- [Frontend](./13-frontend.md)
- [Security](./16-security.md)

