# Security

Security issue нельзя публиковать вместе с реальными prompt data, credentials или exploit payload, содержащим данные заказчика. Канал ответственного раскрытия будет определён владельцем репозитория до публичного распространения проекта.

## Основные гарантии проекта

- строгая проверка CSV и конфигурируемые resource limits;
- masking email, phone, API keys и secret patterns до embeddings/LLM;
- защита от CSV Injection при экспорте;
- no raw prompts/secrets в logs, UI, PDF и external provider payload;
- tenant-scoped resources и архитектурная authorization boundary;
- provider minimization, structured JSON и bounded retry;
- rate limiting и безопасные ошибки;
- immutable run provenance.

Masking снижает риск, но не гарантирует обнаружение всех чувствительных данных. Production deployment требует отдельного решения по SSO/RBAC, retention, encryption, backups, data residency и условиям обработки BotHub/Gemini.

Полная модель угроз, controls и acceptance criteria: [docs/16-security.md](./docs/16-security.md).

## Сообщение о проблеме

До появления утверждённого security contact создайте приватное сообщение владельцу проекта, не прикладывая реальные данные. Не создавайте публичный issue с секретом или customer data.

