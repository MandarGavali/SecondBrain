from langchain_core.documents import Document

from secondbrain.rag.llm.gemini_llm import get_llm

llm = get_llm()


def grade_documents(query: str, documents: list[Document]) -> list[Document]:
    """
    Filters retrieved documents using Gemini.
    Only relevant documents are returned.
    """

    filtered_docs = []

    for doc in documents:

        prompt = f"""
You are a document relevance grader.

User Question:
{query}

Document:
{doc.page_content}

Is this document useful for answering the user's question?

Reply ONLY with:

YES

or

NO
"""

        response = llm.invoke(prompt)

        # FIX: Use startswith instead of exact equality.
        # Gemini sometimes responds with 'YES.' or 'YES,' which caused over-filtering.
        answer_line = response.content.strip().upper().rstrip(".,!- ")
        if answer_line.startswith("YES"):
            filtered_docs.append(doc)

    # Safety fallback
    if len(filtered_docs) == 0:
        return documents

    return filtered_docs