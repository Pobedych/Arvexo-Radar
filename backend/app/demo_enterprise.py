"""Deterministic, internally consistent demo story for the Enterprise MVP.

Every monetary and business-effect value is derived through the same domain
functions used by tests.  The module contains no customer prompt content.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.domain.effectiveness import MethodologyValue, calculate_business_effect

DEMO_PERIOD_FROM = datetime(2026, 7, 1, tzinfo=UTC)
DEMO_PERIOD_TO = datetime(2026, 8, 1, tzinfo=UTC)

DEMO_METHODOLOGY = {
    "average_monthly_fte_cost": 400_000.0,
    "monthly_work_hours_per_fte": 160.0,
    "monthly_work_minutes_per_fte": 9_600.0,
    "include_development_team": False,
    "electricity_price_per_kwh": 8.7,
    "hardware_depreciation_months": 36,
    "currency": "RUB",
    "calculation_period": "month",
    "profitability_thresholds": {"profitable_roi_percent": 20, "needs_review_roi_percent": 0},
    "best_practice_rules": {
        "min_impact_score": 70,
        "min_usage_count": 8,
        "min_user_count": 3,
        "min_success_rate": 0.80,
        "max_error_rate": 0.20,
        "min_confidence_level": 0.60,
        "min_growth_rate": 0.05,
        "min_time_saved_hours": 1.0,
    },
    "data_status": "demo",
}

_METHODOLOGY_VALUE = MethodologyValue(
    average_monthly_fte_cost=Decimal(400000),
    monthly_work_hours_per_fte=Decimal(160),
    currency="RUB",
    calculation_period="month",
    include_development_team=False,
    profitable_roi_percent=Decimal(20),
    needs_review_roi_percent=Decimal(0),
)

DEMO_MODEL_TARIFFS = [
    {
        "model_name": "GigaChat Pro",
        "input_price_per_1m_tokens": 950.0,
        "output_price_per_1m_tokens": 1900.0,
        "currency": "RUB",
        "effective_from": "2026-05-01T00:00:00Z",
        "effective_to": None,
        "is_demo": True,
    },
    {
        "model_name": "YandexGPT 5 Pro",
        "input_price_per_1m_tokens": 1100.0,
        "output_price_per_1m_tokens": 2200.0,
        "currency": "RUB",
        "effective_from": "2026-05-01T00:00:00Z",
        "effective_to": None,
        "is_demo": True,
    },
    {
        "model_name": "Corporate LLM 70B",
        "input_price_per_1m_tokens": 0.0,
        "output_price_per_1m_tokens": 0.0,
        "currency": "RUB",
        "effective_from": "2026-05-01T00:00:00Z",
        "effective_to": None,
        "is_demo": True,
        "cost_note": "Стоимость распределяется через инфраструктуру, GPU и электроэнергию.",
    },
]

DEMO_COST_COMPONENTS = [
    {"id": "cost-token", "name": "Токены внешних моделей", "category": "token", "amount": 510000.0, "currency": "RUB", "period": "month", "allocation_type": "tokens", "agent_id": None, "model_id": None, "department_id": None, "effective_from": "2026-07-01T00:00:00Z", "effective_to": None, "source": "Model tariff × observed tokens", "is_estimated": False, "fixed_shares": {}},
    {"id": "cost-infra", "name": "Внутренняя AI-инфраструктура", "category": "infrastructure", "amount": 240000.0, "currency": "RUB", "period": "month", "allocation_type": "inference_time", "agent_id": None, "model_id": "Corporate LLM 70B", "department_id": None, "effective_from": "2026-07-01T00:00:00Z", "effective_to": None, "source": "FinOps allocation", "is_estimated": True, "fixed_shares": {}},
    {"id": "cost-subscriptions", "name": "Подписки на AI-агентов", "category": "subscription", "amount": 180000.0, "currency": "RUB", "period": "month", "allocation_type": "agent", "agent_id": "report-copilot", "model_id": None, "department_id": None, "effective_from": "2026-07-01T00:00:00Z", "effective_to": None, "source": "Договоры поставщиков", "is_estimated": False, "fixed_shares": {}},
    {"id": "cost-support", "name": "Сопровождение и эксплуатация", "category": "support", "amount": 120000.0, "currency": "RUB", "period": "month", "allocation_type": "requests", "agent_id": None, "model_id": None, "department_id": None, "effective_from": "2026-07-01T00:00:00Z", "effective_to": None, "source": "Оценка владельца платформы", "is_estimated": True, "fixed_shares": {}},
    {"id": "cost-hardware", "name": "Амортизация GPU-серверов", "category": "hardware_depreciation", "amount": 90000.0, "currency": "RUB", "period": "month", "allocation_type": "inference_time", "agent_id": None, "model_id": "Corporate LLM 70B", "department_id": None, "effective_from": "2026-07-01T00:00:00Z", "effective_to": None, "source": "Стоимость оборудования / 36 месяцев", "is_estimated": True, "fixed_shares": {}},
    {"id": "cost-electricity", "name": "Электроэнергия", "category": "electricity", "amount": 30000.0, "currency": "RUB", "period": "month", "allocation_type": "inference_time", "agent_id": None, "model_id": "Corporate LLM 70B", "department_id": None, "effective_from": "2026-07-01T00:00:00Z", "effective_to": None, "source": "kWh × тариф", "is_estimated": True, "fixed_shares": {}},
    {"id": "cost-dev", "name": "Команда разработки", "category": "development_team", "amount": 320000.0, "currency": "RUB", "period": "month", "allocation_type": "fixed_share", "agent_id": None, "model_id": None, "department_id": None, "effective_from": "2026-07-01T00:00:00Z", "effective_to": None, "source": "Опциональная часть методики", "is_estimated": True, "fixed_shares": {"legal-agent": 0.25, "report-copilot": 0.30, "crm-assistant": 0.25, "knowledge-guide": 0.20}},
]

DEMO_BENCHMARKS = [
    {"scenario_id": "contract-review", "scenario_name": "Проверка договоров", "department": "Юридический отдел", "baseline_minutes_without_ai": 68, "actual_minutes_with_ai": 26, "minutes_saved_per_task": 42, "source_type": "A/B-замер", "sample_size": 84, "confidence_level": 0.92, "approved_by": "Владелец юридического процесса", "approved_at": "2026-06-28T10:00:00Z", "is_estimated": False},
    {"scenario_id": "management-report", "scenario_name": "Сбор управленческого отчёта", "department": "Финансы", "baseline_minutes_without_ai": 52, "actual_minutes_with_ai": 24, "minutes_saved_per_task": 28, "source_type": "Данные внутренней системы", "sample_size": 126, "confidence_level": 0.88, "approved_by": "Финансовый контролёр", "approved_at": "2026-06-27T13:30:00Z", "is_estimated": False},
    {"scenario_id": "crm-followup", "scenario_name": "Подготовка follow-up в CRM", "department": "Продажи", "baseline_minutes_without_ai": 14, "actual_minutes_with_ai": 8, "minutes_saved_per_task": 6, "source_type": "Экспертная оценка", "sample_size": 31, "confidence_level": 0.64, "approved_by": None, "approved_at": None, "is_estimated": True},
    {"scenario_id": "policy-search", "scenario_name": "Поиск по регламентам", "department": "HR", "baseline_minutes_without_ai": 18, "actual_minutes_with_ai": 6, "minutes_saved_per_task": 12, "source_type": "Пользовательский опрос", "sample_size": 4, "confidence_level": 0.35, "approved_by": None, "approved_at": None, "is_estimated": True},
]

_AGENT_INPUTS = [
    {"id": "legal-agent", "name": "Агент договоров", "purpose": "Проверка рисков и реквизитов договоров", "departments": ["Юридический отдел", "Закупки"], "roles": ["Юрист", "Специалист по закупкам"], "model": "GigaChat Pro", "tools": ["Корпоративные документы", "Система согласования"], "mau": 124, "requests": 7900, "tool_calls": 11840, "prompt_tokens": 82000000, "completion_tokens": 18000000, "cost": 270000, "error_rate": 0.027, "latency_ms": 1840, "tasks": 620, "minutes": 42, "confidence": 0.92, "estimated": False},
    {"id": "report-copilot", "name": "Report Copilot", "purpose": "Сбор и проверка управленческой отчётности", "departments": ["Финансы", "Операционный блок"], "roles": ["Аналитик", "Руководитель"], "model": "YandexGPT 5 Pro", "tools": ["Корпоративные документы", "BI-платформа", "Проекты"], "mau": 186, "requests": 9600, "tool_calls": 15420, "prompt_tokens": 91000000, "completion_tokens": 24000000, "cost": 360000, "error_rate": 0.041, "latency_ms": 2120, "tasks": 880, "minutes": 28, "confidence": 0.88, "estimated": False},
    {"id": "crm-assistant", "name": "CRM-ассистент", "purpose": "Подготовка follow-up и обновление карточек клиентов", "departments": ["Продажи", "Поддержка"], "roles": ["Менеджер по продажам", "Специалист поддержки"], "model": "Corporate LLM 70B", "tools": ["CRM", "Почта", "Браузер"], "mau": 241, "requests": 10200, "tool_calls": 20760, "prompt_tokens": 122000000, "completion_tokens": 31000000, "cost": 320000, "error_rate": 0.146, "latency_ms": 2980, "tasks": 520, "minutes": 6, "confidence": 0.64, "estimated": True},
    {"id": "knowledge-guide", "name": "Навигатор знаний", "purpose": "Поиск ответов по внутренним регламентам", "departments": ["HR", "ИТ"], "roles": ["HR-партнёр", "Сотрудник"], "model": "Corporate LLM 70B", "tools": ["Корпоративные документы", "HR-система"], "mau": 91, "requests": 700, "tool_calls": 1060, "prompt_tokens": 9000000, "completion_tokens": 2000000, "cost": 220000, "error_rate": 0.083, "latency_ms": 1660, "tasks": 55, "minutes": 12, "confidence": 0.35, "estimated": True},
]


def _build_agent(source: dict[str, object]) -> dict[str, object]:
    effect = calculate_business_effect(
        completed_tasks=int(source["tasks"]),
        minutes_saved_per_task=Decimal(str(source["minutes"])),
        total_ai_cost=Decimal(str(source["cost"])),
        methodology=_METHODOLOGY_VALUE,
        confidence_level=Decimal(str(source["confidence"])),
        is_estimated=bool(source["estimated"]),
    )
    requests = int(source["requests"])
    error_rate = float(source["error_rate"])
    return {
        **source,
        "total_tokens": int(source["prompt_tokens"]) + int(source["completion_tokens"]),
        "successful_requests": round(requests * (1 - error_rate)),
        "failed_requests": round(requests * error_rate),
        "success_rate": round(1 - error_rate, 4),
        "time_saved_minutes": float(effect.time_saved_minutes),
        "time_saved_hours": float(effect.time_saved_hours),
        "fte_saved": float(effect.fte_saved),
        "money_saved": float(effect.money_saved),
        "net_benefit": float(effect.net_benefit),
        "roi": float(effect.roi_percent) if effect.roi_percent is not None else None,
        "payback_ratio": float(effect.payback_ratio) if effect.payback_ratio is not None else None,
        "status": effect.effectiveness_status,
        "period": "2026-07",
        "currency": "RUB",
        "data_status": "estimate" if source["estimated"] else "actual",
    }


DEMO_AGENTS = [_build_agent(item) for item in _AGENT_INPUTS]

DEMO_DEPARTMENTS = [
    {"department": "Юридический отдел", "mau": 105, "requests": 5300, "cost": 230000, "money_saved": 730000, "adoption_rate": 0.81, "confirmed_saving_share": 0.91},
    {"department": "Финансы", "mau": 92, "requests": 5100, "cost": 250000, "money_saved": 565000, "adoption_rate": 0.74, "confirmed_saving_share": 0.86},
    {"department": "Продажи", "mau": 88, "requests": 4300, "cost": 210000, "money_saved": 300000, "adoption_rate": 0.68, "confirmed_saving_share": 0.58},
    {"department": "Поддержка", "mau": 124, "requests": 4900, "cost": 185000, "money_saved": 260000, "adoption_rate": 0.79, "confirmed_saving_share": 0.63},
    {"department": "HR", "mau": 61, "requests": 3300, "cost": 125000, "money_saved": 150000, "adoption_rate": 0.52, "confirmed_saving_share": 0.34},
    {"department": "ИТ", "mau": 172, "requests": 5500, "cost": 170000, "money_saved": 264000, "adoption_rate": 0.87, "confirmed_saving_share": 0.71},
]
for _department in DEMO_DEPARTMENTS:
    _department["net_benefit"] = _department["money_saved"] - _department["cost"]
    _department["roi"] = (_department["net_benefit"] / _department["cost"]) * 100
    _department["requests_per_user"] = _department["requests"] / _department["mau"]

DEMO_TOOLS = [
    {"tool_name": "Корпоративные документы", "category": "documents", "agents": ["legal-agent", "report-copilot", "knowledge-guide"], "usages": 13240, "success_rate": 0.978, "error_rate": 0.022, "avg_latency_ms": 640, "top_scenario": "Проверка договоров", "money_saved": 910000},
    {"tool_name": "CRM", "category": "crm", "agents": ["crm-assistant"], "usages": 7680, "success_rate": 0.846, "error_rate": 0.154, "avg_latency_ms": 1420, "top_scenario": "Follow-up клиенту", "money_saved": 94000},
    {"tool_name": "Браузер", "category": "browser", "agents": ["crm-assistant"], "usages": 5220, "success_rate": 0.912, "error_rate": 0.088, "avg_latency_ms": 1180, "top_scenario": "Проверка компании", "money_saved": 128000},
    {"tool_name": "Почта", "category": "email", "agents": ["crm-assistant"], "usages": 4860, "success_rate": 0.903, "error_rate": 0.097, "avg_latency_ms": 930, "top_scenario": "Подготовка ответа", "money_saved": 176000},
    {"tool_name": "BI-платформа", "category": "internal_system", "agents": ["report-copilot"], "usages": 4120, "success_rate": 0.969, "error_rate": 0.031, "avg_latency_ms": 760, "top_scenario": "Сводный отчёт", "money_saved": 620000},
    {"tool_name": "HR-система", "category": "hr", "agents": ["knowledge-guide"], "usages": 640, "success_rate": 0.917, "error_rate": 0.083, "avg_latency_ms": 710, "top_scenario": "Поиск регламента", "money_saved": 27500},
]

DEMO_SCENARIOS = [
    {"scenario_id": "contract-review", "name": "Проверка договоров", "agent_id": "legal-agent", "department": "Юридический отдел", "completed_tasks": 620, "success_rate": 0.973, "time_saved_hours": 434, "money_saved": 1085000, "confidence": 0.92, "is_estimated": False},
    {"scenario_id": "management-report", "name": "Сбор управленческого отчёта", "agent_id": "report-copilot", "department": "Финансы", "completed_tasks": 880, "success_rate": 0.959, "time_saved_hours": 410.67, "money_saved": 1026666.67, "confidence": 0.88, "is_estimated": False},
    {"scenario_id": "crm-followup", "name": "Подготовка follow-up в CRM", "agent_id": "crm-assistant", "department": "Продажи", "completed_tasks": 520, "success_rate": 0.854, "time_saved_hours": 52, "money_saved": 130000, "confidence": 0.64, "is_estimated": True},
    {"scenario_id": "policy-search", "name": "Поиск по регламентам", "agent_id": "knowledge-guide", "department": "HR", "completed_tasks": 55, "success_rate": 0.917, "time_saved_hours": 11, "money_saved": 27500, "confidence": 0.35, "is_estimated": True},
]

DEMO_INSIGHTS = [
    {"id": "insight-legal", "severity": "positive", "title": "Юридический отдел создаёт 32% денежной экономии при 20% затрат", "recommendation": "Расширить пилот агента договоров на закупки.", "rule": "department_value_share", "is_estimated": False},
    {"id": "insight-crm", "severity": "critical", "title": "CRM-ассистент имеет отрицательный Net Benefit −190 000 ₽", "recommendation": "Снизить ошибки интеграции CRM и пересмотреть объём внутреннего инференса.", "rule": "negative_agent_net_benefit", "is_estimated": True},
    {"id": "insight-hr", "severity": "warning", "title": "HR показывает высокий интерес, но только 34% экономии подтверждено benchmark", "recommendation": "Провести A/B-замер поиска по регламентам.", "rule": "low_confirmed_saving_share", "is_estimated": True},
    {"id": "insight-scale", "severity": "positive", "title": "Масштабирование практики отчётности добавило 320 часов экономии в месяц", "recommendation": "Продолжить внедрение в операционном блоке.", "rule": "practice_adoption_effect", "is_estimated": False},
]

DEMO_MONTHS = [
    {"month": "2026-05", "cost": 980000, "money_saved": 1610000},
    {"month": "2026-06", "cost": 1080000, "money_saved": 1940000},
    {"month": "2026-07", "cost": 1170000, "money_saved": 2269166.67},
]


def request_series(total: int = 28400, days: int = 31) -> list[dict[str, object]]:
    weights = [780 + ((index * 47) % 260) + (120 if index % 7 in {1, 2, 3} else 0) for index in range(days)]
    scale = Decimal(total) / Decimal(sum(weights))
    values = [int(Decimal(value) * scale) for value in weights]
    values[-1] += total - sum(values)
    return [
        {"date": (DEMO_PERIOD_FROM + timedelta(days=index)).date().isoformat(), "requests": value}
        for index, value in enumerate(values)
    ]


DEMO_PRACTICES = [
    {"id": "demo-contract-review", "title": "Проверка договоров по единому чек-листу", "short_description": "Обезличенная последовательность проверки рисков, реквизитов и отклонений от шаблона.", "department_origin": "Юридический отдел", "scenario_id": "contract-review", "detected_at": "2026-06-12T09:00:00Z", "created_at": "2026-06-12T09:00:00Z", "status": "approved", "confidence_score": 92, "impact_score": 96, "adoption_count": 2, "user_count": 124, "usage_count": 7900, "estimated_time_saved": 434, "estimated_fte_saved": 2.71, "estimated_money_saved": 1085000, "tags": ["договоры", "риски", "закупки"], "approved_by": "Экспертный совет", "approved_at": "2026-06-18T12:00:00Z", "recommended_departments": ["Закупки", "Комплаенс"], "is_estimated": False},
    {"id": "demo-reporting", "title": "Сбор управленческого отчёта из нескольких источников", "short_description": "Обезличенный сценарий объединяет данные, проверяет отклонения и готовит резюме.", "department_origin": "Финансы", "scenario_id": "management-report", "detected_at": "2026-05-21T11:00:00Z", "created_at": "2026-05-21T11:00:00Z", "status": "scaling", "confidence_score": 88, "impact_score": 93, "adoption_count": 3, "user_count": 186, "usage_count": 9600, "estimated_time_saved": 410.67, "estimated_fte_saved": 2.57, "estimated_money_saved": 1026666.67, "tags": ["отчёты", "BI", "контроль"], "approved_by": "Финансовый контролёр", "approved_at": "2026-05-28T15:00:00Z", "recommended_departments": ["Операционный блок", "Продажи"], "is_estimated": False},
    {"id": "demo-policy-search", "title": "Ответы сотрудникам по внутренним регламентам", "short_description": "Кандидат на практику поиска пунктов регламента со ссылкой на корпоративный источник.", "department_origin": "HR", "scenario_id": "policy-search", "detected_at": "2026-07-22T08:30:00Z", "created_at": "2026-07-22T08:30:00Z", "status": "detected", "confidence_score": 35, "impact_score": 76, "adoption_count": 0, "user_count": 91, "usage_count": 700, "estimated_time_saved": 11, "estimated_fte_saved": 0.07, "estimated_money_saved": 27500, "tags": ["HR", "регламенты", "поиск"], "approved_by": None, "approved_at": None, "recommended_departments": ["Сервисный центр"], "is_estimated": True},
]

DEMO_ADOPTIONS = {
    "demo-contract-review": [
        {"id": "adoption-contract-procurement", "practice_id": "demo-contract-review", "target_department": "Закупки", "status": "pilot", "recommended_at": "2026-06-19T09:00:00Z", "accepted_at": "2026-06-22T10:00:00Z", "first_usage_at": "2026-07-01T08:00:00Z", "active_users": 18, "usages": 214, "time_saved_after_adoption": 149.8, "money_saved_after_adoption": 374500, "owner": "Руководитель закупок", "comment": "Пилот на договорах поставки"},
    ],
    "demo-reporting": [
        {"id": "adoption-report-ops", "practice_id": "demo-reporting", "target_department": "Операционный блок", "status": "adopted", "recommended_at": "2026-05-29T09:00:00Z", "accepted_at": "2026-06-01T09:00:00Z", "first_usage_at": "2026-06-03T09:00:00Z", "active_users": 44, "usages": 686, "time_saved_after_adoption": 320, "money_saved_after_adoption": 800000, "owner": "Операционный директор", "comment": "Включено в еженедельный цикл"},
        {"id": "adoption-report-sales", "practice_id": "demo-reporting", "target_department": "Продажи", "status": "accepted", "recommended_at": "2026-07-05T09:00:00Z", "accepted_at": "2026-07-08T09:00:00Z", "first_usage_at": None, "active_users": 0, "usages": 0, "time_saved_after_adoption": 0, "money_saved_after_adoption": 0, "owner": "Директор по продажам", "comment": "Подготовка пилота"},
    ],
    "demo-policy-search": [
        {"id": "adoption-policy-service", "practice_id": "demo-policy-search", "target_department": "Сервисный центр", "status": "recommended", "recommended_at": "2026-07-24T09:00:00Z", "accepted_at": None, "first_usage_at": None, "active_users": 0, "usages": 0, "time_saved_after_adoption": 0, "money_saved_after_adoption": 0, "owner": None, "comment": None},
    ],
}
