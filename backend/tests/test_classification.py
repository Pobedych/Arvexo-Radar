from app.domain.classification import classify_text
from app.domain.taxonomy import OTHER_UNKNOWN


def test_matches_email_category() -> None:
    results = classify_text("Напиши ответ клиенту на письмо про доставку")
    assert results[0].category_id == "email_communication"


def test_falls_back_to_other_unknown() -> None:
    results = classify_text("бессвязный набор слов без ключевых терминов")
    assert results == [results[0]]
    assert results[0].category_id == OTHER_UNKNOWN
    assert results[0].confidence == 1.0


def test_multi_label_can_match_more_than_one_category() -> None:
    results = classify_text("Заведи задачу в Jira и обнови статью в Confluence")
    ids = {r.category_id for r in results}
    assert "task_tracking" in ids
    assert "knowledge_docs" in ids
