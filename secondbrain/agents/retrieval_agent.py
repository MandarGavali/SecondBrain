from typing import List
from langchain_core.documents import Document

from secondbrain.utils.logger import logger
from secondbrain.utils.exceptions import RetrievalError
from secondbrain.rag.services.retrieval_service import retrieve_relevant_documents

def run_retrieval_agent(query: str, k: int = 5) -> List[Document]:
    """
    Agentic wrapper for retrieval. 
    Currently simply delegates to the retrieval service, but will eventually
    house routing, query rewriting, and fallback logic.
    """
    try:
        documents = retrieve_relevant_documents(query=query, k=k)
        return documents
    except Exception as e:
        logger.error("Retrieval agent failed to fetch documents.")
        raise RetrievalError(f"Failed to retrieve documents: {e}") from e
