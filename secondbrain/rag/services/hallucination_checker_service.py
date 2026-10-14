from functools import lru_cache

from langchain_core.documents import Document

from secondbrain.rag.llm.gemini_llm import get_llm


@lru_cache(maxsize=1)
def _llm():
    return get_llm()

def check_hallucination(answer: str, documents: list[Document]) -> tuple[bool, str]:
    """
    Checks if the generated answer is grounded in the provided documents.
    Returns a tuple of (is_grounded: bool, verification_reason: str).
    """
    context = "\n\n".join([doc.page_content for doc in documents])
    
    prompt = f"""
You are a hallucination grader.
Given the following context and answer, verify if the answer is completely grounded in the context.

Context:
{context}

Answer:
{answer}

Respond ONLY with YES or NO on the first line, followed by a brief reason on the second line.
"""
    
    response = _llm().invoke(prompt)
    content_lines = response.content.strip().split("\n")
    
    # FIX: Use startswith instead of exact equality.
    # Gemini sometimes responds with 'YES.' or 'YES,' which broke strict == 'YES' checks.
    first_line = content_lines[0].strip().upper().rstrip(".,!- ")
    is_grounded = first_line.startswith("YES")
    reason = content_lines[1].strip() if len(content_lines) > 1 else "No reason provided."
    
    return is_grounded, reason
