from typing import List
from langchain_core.documents import Document

from secondbrain.rag.services.retrieval_service import retrieve_relevant_documents
from secondbrain.utils.exceptions import RetrievalError
from secondbrain.utils.logger import logger

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
    
    try:
        documents = retrieve_relevant_documents(query=query, k=k)
        return documents
    except RetrievalError:
        # Re-raise expected retrieval errors as-is
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in search_documents: {e}")
        raise RetrievalError(f"Unexpected retrieval failure in search_documents: {e}") from e
