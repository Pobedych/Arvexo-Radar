from pathlib import Path

import pytest

from app.infrastructure.reports.pdf_report import (
    ReportCategoryRow,
    ReportContent,
    render_report_pdf,
)

FONT_DIR = Path(__file__).parent / "fixtures" / "fonts"
FONT_REGULAR = str(FONT_DIR / "DejaVuSans.ttf")
FONT_BOLD = str(FONT_DIR / "DejaVuSans-Bold.ttf")


@pytest.mark.skipif(not FONT_DIR.exists(), reason="test font fixtures not available")
def test_renders_valid_pdf_with_cyrillic_content() -> None:
    content = ReportContent(
        dataset_name="Тестовый датасет",
        run_id="run-1",
        status="completed",
        generated_at="2026-07-25T00:00:00Z",
        total_records=10,
        top_categories=[ReportCategoryRow("Работа с почтой", 5, 0.5)],
    )

    pdf_bytes = render_report_pdf(
        content, font_regular_path=FONT_REGULAR, font_bold_path=FONT_BOLD
    )

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000


@pytest.mark.skipif(not FONT_DIR.exists(), reason="test font fixtures not available")
def test_renders_with_empty_sections() -> None:
    content = ReportContent(
        dataset_name="Пустой датасет",
        run_id="run-2",
        status="completed",
        generated_at="2026-07-25T00:00:00Z",
        total_records=0,
    )

    pdf_bytes = render_report_pdf(
        content, font_regular_path=FONT_REGULAR, font_bold_path=FONT_BOLD
    )

    assert pdf_bytes.startswith(b"%PDF-")
