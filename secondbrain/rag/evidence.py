import os
from langchain_core.documents import Document


def doc_to_evidence(doc: Document, score: float | None) -> dict:
    md = doc.metadata or {}
    source = str(md.get("source", ""))
    return {
        "text": doc.page_content,
        "page": str(md.get("page_label", md.get("page", "N/A"))),
        "document": md.get("document_name") or (os.path.basename(source) if source else "unknown"),
        "source": source,
        "chunk_id": md.get("chunk_id"),
        "score": float(score) if score is not None else None,
    }


def evidence_to_doc(e: dict) -> Document:
    return Document(
        page_content=e["text"],
        metadata={
            "page_label": e.get("page"),
            "source": e.get("source") or e.get("document"),
            "document_name": e.get("document"),
            "chunk_id": e.get("chunk_id"),
        },
    )


def build_sources(evidence: list[dict]) -> list[dict]:
    """De-duplicate by (document, page), keep the best score, sort by score desc."""
    best: dict[tuple, dict] = {}
    for e in evidence or []:
        key = (e.get("document"), e.get("page"))
        score = e.get("score")
        if key not in best or (score or 0) > (best[key].get("score") or 0):
            best[key] = {"document": e.get("document"), "page": e.get("page"), "score": score}
    return sorted(best.values(), key=lambda s: s.get("score") or 0, reverse=True)
