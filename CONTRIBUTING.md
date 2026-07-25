# Contributing to Arvexo Radar

## 1. Documentation-first

Документация в `docs/` — Single Source of Truth. Не реализуйте поведение, отсутствующее в утверждённых Functional Requirements, Architecture, API и Security. Противоречие сначала фиксируется и разрешается минимальным изменением спецификации.

## 2. Scope

- Не меняйте зафиксированный стек без ADR и согласования.
- Не добавляйте внешние сервисы/библиотеки без необходимости и зафиксированного решения.
- Не включайте post-MVP возможности в текущий scope молча.
- Не используйте реальные customer prompts в fixtures, issues, logs или screenshots.

## 3. Branches и commits

Рекомендуемый branch prefix: `codex/` для Codex-generated branches; для остальных участников — согласованный repository convention.

Conventional commits:

```text
docs(spec): define business problem
docs(architecture): add system architecture
feat(api): implement dataset upload
feat(ai): add scenario clustering
fix(security): prevent csv injection
```

Commit должен быть атомарным и не смешивать несвязанные изменения.

## 4. Code quality

- type hints в Python и strict TypeScript boundaries;
- Pydantic validation для API/provider contracts;
- безопасные, типизированные ошибки;
- migrations для schema changes;
- no critical TODO вместо поведения;
- no raw prompt/secret in logs;
- no direct dependency domain logic → provider SDK.

## 5. Tests

Изменение должно включать релевантные unit/integration/e2e/security tests. Критические области: upload validation, masking, CSV Injection, state transitions, provider schema, tenant isolation, long-request chunking и evidence traceability.

Не указывайте тест как пройденный, если он не запускался. После появления кода README будет содержать authoritative команды.

## 6. Documentation changes

- используйте один термин последовательно;
- не дублируйте подробный текст между root docs и `docs/`;
- добавляйте acceptance criteria и edge cases;
- не создавайте фиктивные metrics/benchmarks;
- обновляйте ADR при изменении существенного решения;
- проверяйте относительные Markdown links.

## 7. Security

Следуйте [SECURITY.md](./SECURITY.md). Не коммитьте `.env`, API keys, raw datasets, reports с customer data или model cache с чувствительными артефактами.

## 8. Pull request checklist

- [ ] Изменение прослеживается до требования.
- [ ] Scope и ADR согласованы.
- [ ] Tests добавлены и фактически запущены.
- [ ] Logs/errors/output проверены на утечки.
- [ ] Documentation и changelog обновлены при изменении поведения.
- [ ] Local/mock mode сохранён.
- [ ] Migration/rollback impact описан.

