from app.domain.dataset_validation import parse_and_validate
from app.domain.enums import RecordStatus, ValidationCode


def _csv(text: str) -> bytes:
    return text.encode("utf-8")


def test_empty_file_is_rejected_v001() -> None:
    result = parse_and_validate(_csv(""), max_row_chars=10_000)
    assert result.dataset_rejection_code == ValidationCode.V001_EMPTY_FILE.value


def test_missing_text_column_is_rejected_v002() -> None:
    result = parse_and_validate(_csv("id,team\n1,Sales\n"), max_row_chars=10_000)
    assert result.dataset_rejection_code == ValidationCode.V002_MISSING_TEXT_MAPPING.value


def test_empty_text_row_rejected_v003() -> None:
    result = parse_and_validate(_csv('text\n"   "\n'), max_row_chars=10_000)
    assert result.rows[0].status is RecordStatus.REJECTED
    assert result.rows[0].rejection_code == ValidationCode.V003_EMPTY_TEXT.value


def test_row_too_long_rejected_v007() -> None:
    long_text = "a" * 50
    result = parse_and_validate(_csv(f"text\n{long_text}\n"), max_row_chars=10)
    assert result.rows[0].status is RecordStatus.REJECTED
    assert result.rows[0].rejection_code == ValidationCode.V007_ROW_TOO_LONG.value


def test_unknown_fields_tracked_v008() -> None:
    result = parse_and_validate(_csv("text,mystery\nHello,x\n"), max_row_chars=10_000)
    assert "mystery" in result.unknown_fields
    assert result.rows[0].status is RecordStatus.ACCEPTED


def test_invalid_timestamp_accepted_with_warning_v005() -> None:
    result = parse_and_validate(
        _csv("text,timestamp\nHello,not-a-date\n"), max_row_chars=10_000
    )
    row = result.rows[0]
    assert row.status is RecordStatus.ACCEPTED_WITH_WARNINGS
    assert "invalid_timestamp" in row.warnings
    assert row.trend_eligible is False


def test_valid_timestamp_marks_trend_eligible() -> None:
    result = parse_and_validate(
        _csv("text,timestamp\nHello,2026-07-01T09:00:00+03:00\n"), max_row_chars=10_000
    )
    row = result.rows[0]
    assert row.status is RecordStatus.ACCEPTED
    assert row.trend_eligible is True
    assert row.timestamp is not None


def test_no_valid_rows_flags_v009() -> None:
    result = parse_and_validate(_csv('text\n""\n'), max_row_chars=10_000)
    assert result.dataset_rejection_code == ValidationCode.V009_NO_VALID_ROWS.value


def test_duplicate_request_id_with_different_text_is_conflict_v006() -> None:
    csv_text = "request_id,text\nr-1,Hello world\nr-1,Different text entirely\n"
    result = parse_and_validate(_csv(csv_text), max_row_chars=10_000)
    assert "r-1" in result.conflicting_request_ids
    assert result.has_conflict is True


def test_duplicate_request_id_with_same_text_is_not_conflict() -> None:
    csv_text = "request_id,text\nr-1,Hello world\nr-1,Hello world\n"
    result = parse_and_validate(_csv(csv_text), max_row_chars=10_000)
    assert result.has_conflict is False


def test_accepted_row_text_is_masked() -> None:
    result = parse_and_validate(_csv("text\nContact me at a@b.com\n"), max_row_chars=10_000)
    row = result.rows[0]
    assert "a@b.com" not in row.masked_text
    assert "[EMAIL_1]" in row.masked_text
    assert "sensitive_data_masked" in row.warnings
    assert row.status is RecordStatus.ACCEPTED_WITH_WARNINGS


def test_semicolon_delimiter_detected() -> None:
    result = parse_and_validate(
        _csv("text;team\nHello there;Sales\n"), max_row_chars=10_000
    )
    assert result.dataset_rejection_code is None
    assert result.rows[0].status is RecordStatus.ACCEPTED


def test_counts_are_consistent_with_row_count() -> None:
    csv_text = "text\nHello\n\"   \"\nWorld\n"
    result = parse_and_validate(_csv(csv_text), max_row_chars=10_000)
    assert result.accepted + result.accepted_with_warnings + result.rejected == len(result.rows)
    assert len(result.rows) == 3
