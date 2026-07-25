import unicodedata

from app.domain.normalization import normalize_text


def test_crlf_normalized_to_lf() -> None:
    assert normalize_text("line1\r\nline2") == "line1\nline2"


def test_strips_outer_whitespace() -> None:
    assert normalize_text("  hello  ") == "hello"


def test_removes_control_characters_but_keeps_tab_and_newline() -> None:
    text = "a\x00b\x07c\td\ne"
    assert normalize_text(text) == "abc\td\ne"


def test_nfc_normalization() -> None:
    composed = "é"[:1] + "́"  # placeholder, overwritten below
    composed = unicodedata.normalize("NFC", "é")
    decomposed = unicodedata.normalize("NFD", composed)

    assert decomposed != composed  # sanity check the fixture is meaningful
    assert normalize_text(decomposed) == composed
