import re

from secondbrain.config import settings
from secondbrain.core.logger import get_logger

logger = get_logger("routing.classifier")

NO_SEARCH, SIMPLE, COMPLEX = "no_search", "simple", "complex"
VALID_LABELS = {NO_SEARCH, SIMPLE, COMPLEX}

_SMALL_TALK = re.compile(
    r"^\s*(hi|hello|hey|thanks|thank you|ok|okay|good (morning|afternoon|evening)|bye|"
    r"who are you|what can you do)\b[\s!.?]*$",
    re.IGNORECASE,
)
_COMPLEX_HINTS = re.compile(
    r"\b(compare|comparison|difference between|differences|versus|vs\.?|across|"
    r"all (the )?(documents|files|pdfs)|every|summari[sz]e|overview|why|how (do|does|would|can)|"
    r"trade-?offs?|pros and cons|list all|step[- ]by[- ]step|relationship|impact|"
    r"analy[sz]e|evaluate|generate|interview questions)\b",
    re.IGNORECASE,
)
_SIMPLE_HINTS = re.compile(
    r"^\s*(what|when|where|who|which|how many|how much|is|are|does|do|define|list)\b",
    re.IGNORECASE,
)

_LLM_PROMPT = """Classify the user's message for a document question-answering assistant.
Answer with exactly one word.

no_search - greeting, thanks, chit-chat, or a general question that is not about the user's documents or personal memory
simple - a single-fact lookup answerable from one passage of the user's documents
complex - needs several passages, comparison, summary, reasoning or multiple steps, or needs tools such as listing documents or generating questions

Message: {query}
Answer:"""


def heuristic_classify(query: str) -> tuple[str | None, str]:
    """Return (label or None if unsure, reason)."""
    q = (query or "").strip()
    if not q:
        return NO_SEARCH, "empty"
    if _SMALL_TALK.match(q):
        return NO_SEARCH, "small_talk"
    words = len(q.split())
    if _COMPLEX_HINTS.search(q) or words > 25 or q.count("?") > 1:
        return COMPLEX, "complex_hint"
    if _SIMPLE_HINTS.match(q) and words <= 14:
        return SIMPLE, "simple_hint"
    return None, "uncertain"


def _llm_text(prompt: str) -> str:
    from secondbrain.rag.llm.gemini_llm import get_llm
    from secondbrain.utils.text import message_text

    return message_text(get_llm().invoke(prompt).content)


def llm_classify(query: str, llm_call=None) -> str | None:
    llm_call = llm_call or _llm_text
    try:
        raw = llm_call(_LLM_PROMPT.format(query=query)).strip().lower()
    except Exception as e:  # network/quota/etc. -> caller falls back to COMPLEX
        logger.warning(f"LLM classifier failed: {e}")
        return None
    token = re.split(r"[^a-z_]+", raw.replace(" ", "_"))[0] if raw else ""
    for label in VALID_LABELS:
        if token.startswith(label):
            return label
    return None


def classify_query(query: str, llm_call=None) -> dict:
    """Return {'label', 'method', 'reason'}.  Never raises; unsure -> COMPLEX."""
    mode = (settings.router_mode or "hybrid").lower()
    try:
        if mode in ("heuristic", "hybrid"):
            label, reason = heuristic_classify(query)
            if label:
                return {"label": label, "method": "heuristic", "reason": reason}
            if mode == "heuristic":
                return {"label": COMPLEX, "method": "heuristic", "reason": "uncertain->complex"}
        label = llm_classify(query, llm_call)
        if label:
            return {"label": label, "method": "llm", "reason": "zero_shot"}
    except Exception as e:
        logger.warning(f"classify_query failed: {e}")
    return {"label": COMPLEX, "method": "fallback", "reason": "default_complex"}
