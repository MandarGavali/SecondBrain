from secondbrain.rag.llm.gemini_llm import get_llm

llm = get_llm()

def rewrite_query(query: str) -> str:
    """
    Rewrites the user's query to improve document retrieval.
    """

    prompt = f"""
Rewrite the user's query to improve document retrieval.

Do NOT answer the question.

Only rewrite it so that a vector database can retrieve better documents.

Original Query:

{query}

Return only the rewritten query.
"""

    response = llm.invoke(prompt)

    return response.content.strip()
