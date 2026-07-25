from app.domain.prompt_health import (
    RULE_DUPLICATE,
    RULE_SENSITIVE_DATA,
    RULE_TOO_SHORT,
    RecordForHealthCheck,
    evaluate_findings,
)


def test_too_short_flagged() -> None:
    records = [RecordForHealthCheck("r1", "ок", 1, ())]
    findings = evaluate_findings(records)
    assert any(f.rule_id == RULE_TOO_SHORT for f in findings)


def test_duplicate_flagged_for_both_records() -> None:
    records = [
        RecordForHealthCheck("r1", "одинаковый текст запроса", 10, ()),
        RecordForHealthCheck("r2", "одинаковый текст запроса", 10, ()),
    ]
    findings = evaluate_findings(records)
    duplicate_ids = {f.record_id for f in findings if f.rule_id == RULE_DUPLICATE}
    assert duplicate_ids == {"r1", "r2"}


def test_sensitive_data_warning_becomes_security_finding() -> None:
    records = [
        RecordForHealthCheck("r1", "напиши [EMAIL_1]", 10, ("sensitive_data_masked",))
    ]
    findings = evaluate_findings(records)
    sec = [f for f in findings if f.rule_id == RULE_SENSITIVE_DATA]
    assert len(sec) == 1
    assert sec[0].type == "security"
