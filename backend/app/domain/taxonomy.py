"""Category taxonomy v1 (docs/10-ai-pipeline.md section 6, docs/08-dataset.md).

Fixed for the Hackathon MVP and versioned as a whole (`TAXONOMY_VERSION`),
not per-category, since docs/09-architecture.md defers algorithm/taxonomy
tuning to a reference-dataset benchmark that hasn't happened yet. Topics are
drawn from the КРОК case examples (email, CRM, Jira, Confluence, calendar,
reporting, project management) as *themes*, not a confirmed customer
taxonomy — see docs/08-dataset.md DATA-AC-06.
"""

from __future__ import annotations

from dataclasses import dataclass

TAXONOMY_VERSION = "taxonomy-v1"

OTHER_UNKNOWN = "other_unknown"


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    keywords: tuple[str, ...]


CATEGORIES: tuple[Category, ...] = (
    Category(
        id="email_communication",
        name="Работа с почтой и коммуникациями",
        keywords=("письм", "почт", "email", "рассылк", "ответ клиенту", "переписк"),
    ),
    Category(
        id="crm_sales",
        name="CRM и продажи",
        keywords=("crm", "сделк", "клиент", "лид", "продаж", "воронк"),
    ),
    Category(
        id="task_tracking",
        name="Задачи и трекинг (Jira)",
        keywords=("jira", "задач", "тикет", "спринт", "баг", "issue"),
    ),
    Category(
        id="knowledge_docs",
        name="Документация и база знаний (Confluence)",
        keywords=("confluence", "документац", "статья", "вики", "wiki", "инструкц"),
    ),
    Category(
        id="calendar_scheduling",
        name="Календарь и планирование встреч",
        keywords=("встреч", "календар", "расписан", "созвон", "митинг", "meeting"),
    ),
    Category(
        id="reporting_analytics",
        name="Отчётность и аналитика",
        keywords=("отчёт", "отчет", "сводк", "аналитик", "дашборд", "метрик"),
    ),
    Category(
        id="project_management",
        name="Управление проектами",
        keywords=("проект", "план", "дедлайн", "milestone", "роадмап", "roadmap"),
    ),
    Category(
        id=OTHER_UNKNOWN,
        name="Другое / неопределено",
        keywords=(),
    ),
)

CATEGORY_BY_ID = {c.id: c for c in CATEGORIES}
