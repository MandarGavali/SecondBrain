from typing import List
from langchain_core.documents import Document

from secondbrain.core.logger import get_logger

logger = get_logger("rag.services.retrieval")
from secondbrain.core.exceptions import RetrieverError
from secondbrain.rag.embeddings.gemini_embeddings import get_embedding_model
from secondbrain.rag.vectorstore.qdrant_store import get_existing_vector_store
from secondbrain.rag.retriever.retriever import retrieve_documents as raw_retrieve_documents

# Singleton cache for expensive objects
_embedding_model = None
_vector_store = None

def _get_vector_store():
    """
    Helper to lazily initialize and cache the embedding model and vector store connection.
    This avoids recreating expensive connections and objects on every single query.
    """
    global _embedding_model, _vector_store
    try:
        if _embedding_model is None:
            logger.info("Initializing embedding model cache.")
            _embedding_model = get_embedding_model()
        if _vector_store is None:
            logger.info("Initializing vector store cache.")
            _vector_store = get_existing_vector_store(_embedding_model)
        return _vector_store
    except Exception as e:
        logger.exception("Failed to initialize vector store or embeddings.")
        raise RetrieverError(f"Infrastructure connection failed: {e}") from e

def retrieve_relevant_documents(query: str, k: int = 5) -> List[Document]:
    """
    Retrieves documents relevant to the query.
    This function abstracts away the underlying embedding and vector store initialization.
    """
    logger.info("Retriever started")
    try:
        vector_store = _get_vector_store()
        documents = raw_retrieve_documents(query=query, vector_store=vector_store, k=k)
        logger.info("Documents retrieved")
        logger.info(f"Number of documents: {len(documents)}")
        logger.info("Retriever finished")
        return documents
    except Exception as e:
        logger.exception("Error occurred during document retrieval.")
        raise RetrieverError(f"Document retrieval failed: {e}") from e
