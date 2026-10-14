import re

from secondbrain.config import settings


def retrieval_strength(scores: list[float]) -> float:
    """s_top: best similarity, clipped to [0, 1]."""
    if not scores:
        return 0.0
    return max(0.0, min(1.0, max(scores)))


def relevance_ratio(scores: list[float], min_score: float | None = None) -> float:
    """r: share of retrieved chunks whose similarity >= min_score."""
    if not scores:
        return 0.0
    min_score = settings.score_rel_min if min_score is None else min_score
    return sum(1 for s in scores if s >= min_score) / len(scores)


def compute_confidence(
    scores: list[float],
    grounded: bool | None,
    w_ret: float | None = None,
    w_rel: float | None = None,
    w_grd: float | None = None,
) -> float:
    """C = w1*s_top + w2*r + w3*g.  If g is None (check skipped) the weights are renormalised."""
    w_ret = settings.w_retrieval if w_ret is None else w_ret
    w_rel = settings.w_relevance if w_rel is None else w_rel
    w_grd = settings.w_grounded if w_grd is None else w_grd

    parts = [(w_ret, retrieval_strength(scores)), (w_rel, relevance_ratio(scores))]
    if grounded is not None:
        parts.append((w_grd, 1.0 if grounded else 0.0))
    total = sum(w for w, _ in parts)
    if total <= 0:
        return 0.0
    return round(sum(w * v for w, v in parts) / total, 4)


def label_for(score: float, high: float | None = None, medium: float | None = None) -> str:
    high = settings.conf_high if high is None else high
    medium = settings.conf_medium if medium is None else medium
    if score >= high:
        return "High"
    if score >= medium:
        return "Medium"
    return "Low"


def decide(
    grounded: bool | None,
    score: float,
    retries: int,
    max_retries: int | None = None,
    abstain_below: float | None = None,
) -> str:
    """Return 'deliver' | 'retry' | 'abstain'."""
    max_retries = settings.max_retries if max_retries is None else max_retries
    abstain_below = settings.conf_abstain if abstain_below is None else abstain_below
    failing = (grounded is False) or (score < abstain_below)
    if not failing:
        return "deliver"
    return "retry" if retries < max_retries else "abstain"


# The generation prompt asks the LLM for a verbal "Confidence: High/Medium/Low" line.
# We replace it with the measured confidence, so strip the verbal one from the answer text.
_VERBAL = re.compile(r"\s*\**Confidence\**\s*:?\s*\**\s*(High|Medium|Low)\b[^\n]*\s*$", re.IGNORECASE)


def strip_verbal_confidence(text: str) -> str:
    return _VERBAL.sub("", text or "").rstrip()
