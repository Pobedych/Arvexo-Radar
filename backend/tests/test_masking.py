from app.domain.masking import mask_text


def test_masks_email() -> None:
    result = mask_text("Напиши ответ для user@example.com по задаче")
    assert "user@example.com" not in result.masked_text
    assert "[EMAIL_1]" in result.masked_text
    assert result.findings[0].kind == "EMAIL"


def test_masks_phone() -> None:
    result = mask_text("Позвони мне на +7 999 123-45-67 сегодня")
    assert "999 123-45-67" not in result.masked_text
    assert "[PHONE_1]" in result.masked_text


def test_masks_secret_like_token() -> None:
    result = mask_text("ключ sk-abcdefghij1234567890 не публикуй")
    assert "sk-abcdefghij1234567890" not in result.masked_text
    assert "[SECRET_1]" in result.masked_text


def test_no_false_positive_on_plain_text() -> None:
    result = mask_text("Собери сводку писем за день")
    assert result.masked_text == "Собери сводку писем за день"
    assert result.findings == ()


def test_multiple_findings_get_incrementing_placeholders() -> None:
    result = mask_text("a@b.com и c@d.com")
    assert "[EMAIL_1]" in result.masked_text
    assert "[EMAIL_2]" in result.masked_text
