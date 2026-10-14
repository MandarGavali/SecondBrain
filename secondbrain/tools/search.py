from typing import List
from langchain_core.documents import Document

from secondbrain.rag.evidence import doc_to_evidence
from secondbrain.rag.services.retrieval_service import retrieve_relevant_documents, retrieve_with_scores
from secondbrain.core.logger import get_logger

logger = get_logger("tools.search")

def search_documents(query: str, k: int = 5) -> List[Document]:
    """
    Searches the indexed knowledge base and returns the most relevant LangChain Document objects.

    This tool is a pure retrieval function and does not call any LLM, generate responses,
    summarize content, or modify retrieved documents.

    Args:
        query (str): The search query to locate relevant documents.
        k (int, optional): The number of relevant documents to retrieve. Defaults to 5.

    Returns:
        List[Document]: A list of retrieved LangChain Document objects.

    Raises:
        ValueError: If the query is empty or contains only whitespace.
        RetrievalError: If document retrieval or database connection fails.
    """
    if not query or not query.strip():
        logger.error("Search query is empty or blank.")
        raise ValueError("Query cannot be empty or blank.")

    logger.info(f"search_documents tool invoked with query='{query}' and k={k}")
    
    return retrieve_relevant_documents(query=query, k=k)  # raises RetrieverError on failure


def search_documents_evidence(query: str, k: int = 5) -> tuple[str, list[dict]]:
    """Agent-facing search. Returns (text for the LLM, evidence list kept as the tool artifact)."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty or blank.")
    pairs = retrieve_with_scores(query=query, k=k)
    evidence = [doc_to_evidence(doc, score) for doc, score in pairs]
    if not evidence:
        return "No relevant passages found.", []
    blocks = [
        f"[{i}] {e['document']} - page {e['page']} (similarity {e['score']:.2f})\n{e['text']}"
        for i, e in enumerate(evidence, start=1)
    ]
    return "\n\n".join(blocks), evidence
