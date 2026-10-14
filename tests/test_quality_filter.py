from langchain_core.documents import Document
from secondbrain.rag.processors.quality_filter import filter_chunks


def _d(t):
    return Document(page_content=t, metadata={})


def test_filters_short_toc_lowalpha_duplicates():
    good = "Employees may work from home up to three days per week with manager approval. " * 2
    chunks = [
        _d(good),
        _d(good),                                   # duplicate
        _d("Page 3"),                               # too short
        _d("1 2 3 4 5 6 7 8 9 0 " * 10),            # low alpha
        _d("Introduction ........ 1 Scope ........ 2 Terms ........ 3 Annex ........ 4 " * 2),  # toc
    ]
    kept, stats = filter_chunks(chunks, min_chars=60, min_alpha=0.55)
    assert len(kept) == 1
    assert stats["total"] == 5 and stats["kept"] == 1
    assert set(stats["reasons"]) == {"duplicate", "too_short", "low_alpha", "toc_like"}
    assert 0 < kept[0].metadata["quality_score"] <= 1
