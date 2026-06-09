from backend.app.retrieval.bm25 import BM25Index


def test_bm25_returns_relevant_document_first():
    index = BM25Index(
        [
            ("a", "microwave absorber ferrite magnetic loss"),
            ("b", "optical coating refractive index"),
        ]
    )
    results = index.search("ferrite magnetic microwave")
    assert results[0][0] == "a"
