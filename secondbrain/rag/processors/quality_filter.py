import hashlib
import re
from collections import Counter

from langchain_core.documents import Document

from secondbrain.config import settings

_DOT_LEADER = re.compile(r"\.{4,}|(?:\.\s){4,}")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def alpha_ratio(text: str) -> float:
    if not text:
        return 0.0
    return sum(ch.isalpha() for ch in text) / len(text)


def looks_like_toc(text: str) -> bool:
    """Table-of-contents / index lines: many dot leaders."""
    return len(_DOT_LEADER.findall(text or "")) >= 3


def score_chunk(text: str) -> float:
    norm = _normalize(text)
    length_part = min(1.0, len(norm) / 500.0)
    alpha_part = min(1.0, alpha_ratio(norm) / 0.8)
    return round(0.5 * length_part + 0.5 * alpha_part, 3)


def filter_chunks(
    chunks: list[Document],
    min_chars: int | None = None,
    min_alpha: float | None = None,
) -> tuple[list[Document], dict]:
    """Stage-1 verification at ingestion time. Returns (kept_chunks, stats)."""
    min_chars = settings.quality_min_chars if min_chars is None else min_chars
    min_alpha = settings.quality_min_alpha if min_alpha is None else min_alpha

    kept: list[Document] = []
    reasons: Counter = Counter()
    seen: set[str] = set()

    for chunk in chunks:
        raw = chunk.page_content or ""
        norm = _normalize(raw)
        reason = None
        if len(norm) < min_chars:
            reason = "too_short"
        elif looks_like_toc(raw):  # before low_alpha: dot leaders always push alpha below the cut-off
            reason = "toc_like"
        elif alpha_ratio(norm) < min_alpha:
            reason = "low_alpha"
        else:
            digest = hashlib.md5(norm.encode("utf-8")).hexdigest()
            if digest in seen:
                reason = "duplicate"
            else:
                seen.add(digest)

        if reason:
            reasons[reason] += 1
            continue
        chunk.metadata["quality_score"] = score_chunk(raw)
        kept.append(chunk)

    stats = {
        "total": len(chunks),
        "kept": len(kept),
        "rejected": len(chunks) - len(kept),
        "reasons": dict(reasons),
    }
    return kept, stats
