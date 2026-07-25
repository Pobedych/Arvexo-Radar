from app.domain.clustering import cluster_records
from app.domain.embeddings import embed_text


def test_similar_texts_cluster_together_and_dissimilar_dont() -> None:
    vectors = {
        "r1": embed_text("Собери сводку писем за день"),
        "r2": embed_text("Собери сводку писем за неделю"),
        "r3": embed_text("Составь краткую выжимку по письмам"),
        "r4": embed_text("Покажи мои задачи в Jira по приоритету"),
        "r5": embed_text("Список задач в Jira с высоким приоритетом"),
        "r6": embed_text("Задачи в Jira сортированные по приоритету"),
    }

    clusters = cluster_records(vectors, similarity_threshold=0.2, min_cluster_size=2)

    non_noise = [c for c in clusters if not c.is_noise]
    assert len(non_noise) >= 1
    all_members = {m for c in clusters for m in c.member_ids}
    assert all_members == set(vectors.keys())


def test_small_cluster_marked_as_noise() -> None:
    vectors = {
        "r1": embed_text("уникальный текст один"),
        "r2": embed_text("совершенно другой текст два"),
    }
    clusters = cluster_records(vectors, similarity_threshold=0.99, min_cluster_size=3)
    assert all(c.is_noise for c in clusters)
