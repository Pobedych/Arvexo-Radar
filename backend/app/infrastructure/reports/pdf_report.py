"""PDF report rendering (docs/11-dashboard.md section 14, docs/15-api.md
reports endpoints).

Uses fpdf2 with an embedded DejaVu Sans TTF rather than the PDF base-14
fonts: base-14 fonts have no Cyrillic glyphs at all, and this product's
primary content language is Russian. Font files are provided by the
`fonts-dejavu-core` package in the Docker image (see Dockerfile) rather than
bundled in the repo, to avoid shipping font binaries in git.

All text comes from already-masked, already-escaped domain data (categories,
scenario names, insight statements); fpdf2 itself escapes PDF string
content, so no separate sanitization step is needed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fpdf import FPDF

from app.domain.errors import ReportGenerationError

TITLE_SIZE = 16
HEADING_SIZE = 13
BODY_SIZE = 10


@dataclass
class ReportCategoryRow:
    name: str
    count: int
    share: float


@dataclass
class ReportScenarioRow:
    name: str
    description: str | None
    size: int
    share: float


@dataclass
class ReportInsightRow:
    type: str
    statement: str
    confidence: float


@dataclass
class ReportRecommendationRow:
    action: str
    rationale: str


@dataclass
class ReportContent:
    dataset_name: str
    run_id: str
    status: str
    generated_at: str
    total_records: int
    top_categories: list[ReportCategoryRow] = field(default_factory=list)
    top_scenarios: list[ReportScenarioRow] = field(default_factory=list)
    insights: list[ReportInsightRow] = field(default_factory=list)
    recommendations: list[ReportRecommendationRow] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    degradation_notes: list[str] = field(default_factory=list)


def render_report_pdf(
    content: ReportContent,
    *,
    font_regular_path: str,
    font_bold_path: str,
) -> bytes:
    try:
        pdf = FPDF(format="A4")
        pdf.add_font("DejaVu", "", font_regular_path)
        pdf.add_font("DejaVu", "B", font_bold_path)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("DejaVu", "B", TITLE_SIZE)
        pdf.multi_cell(0, 10, "Arvexo Radar — отчёт по анализу", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("DejaVu", "", BODY_SIZE)
        pdf.multi_cell(
            0,
            6,
            f"Датасет: {content.dataset_name}\n"
            f"Run ID: {content.run_id}\n"
            f"Статус: {content.status}\n"
            f"Сформирован: {content.generated_at}\n"
            f"Обработано записей: {content.total_records}",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(4)

        _section(pdf, "Топ категорий")
        if content.top_categories:
            for c in content.top_categories:
                _bullet(pdf, f"{c.name}: {c.count} записей ({c.share:.0%})")
        else:
            _bullet(pdf, "Нет данных.")

        _section(pdf, "Топ сценариев")
        if content.top_scenarios:
            for s in content.top_scenarios:
                line = f"{s.name}: {s.size} записей ({s.share:.0%})"
                if s.description:
                    line += f" — {s.description}"
                _bullet(pdf, line)
        else:
            _bullet(pdf, "Устойчивые сценарии не обнаружены.")

        _section(pdf, "Инсайты")
        if content.insights:
            for i in content.insights:
                label = "Наблюдение" if i.type == "observation" else "Гипотеза"
                _bullet(pdf, f"[{label}, confidence={i.confidence:.2f}] {i.statement}")
        else:
            _bullet(pdf, "Недостаточно данных для инсайтов.")

        _section(pdf, "Рекомендации")
        if content.recommendations:
            for r in content.recommendations:
                _bullet(pdf, f"{r.action} — {r.rationale}")
        else:
            _bullet(pdf, "Рекомендации не сформированы.")

        if content.degradation_notes:
            _section(pdf, "Деградация анализа")
            for note in content.degradation_notes:
                _bullet(pdf, note)

        _section(pdf, "Ограничения")
        for limitation in content.limitations:
            _bullet(pdf, limitation)

        return bytes(pdf.output())
    except Exception as exc:
        raise ReportGenerationError(
            "Failed to render PDF report.", details={}
        ) from exc


def _section(pdf: FPDF, title: str) -> None:
    pdf.ln(3)
    pdf.set_font("DejaVu", "B", HEADING_SIZE)
    pdf.multi_cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", BODY_SIZE)


def _bullet(pdf: FPDF, text: str) -> None:
    pdf.multi_cell(0, 6, f"• {text}", new_x="LMARGIN", new_y="NEXT")
