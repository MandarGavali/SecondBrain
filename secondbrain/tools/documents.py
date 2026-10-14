import os
from typing import List

from secondbrain.rag.services.retrieval_service import _get_vector_store
from secondbrain.rag.vectorstore.qdrant_store import collection_exists
from secondbrain.core.exceptions import RetrievalError
from secondbrain.core.logger import get_logger

logger = get_logger("tools.documents")

def list_documents() -> List[str]:
    """
    Returns all indexed document names from the knowledge base.
    
    This function accesses the vector store directly to retrieve unique metadata sources 
    across all indexed chunks. It sorts the filenames alphabetically and removes duplicates.
    It does not generate summaries or call the LLM.

    Returns:
        List[str]: An alphabetically sorted list of unique filenames present in the vector store.
                   Returns an empty list if no documents exist.
                   
    Raises:
        RetrievalError: If the vector store connection or scrolling fails.
    """
    logger.info("list_documents tool invoked")
    
    try:
        if not collection_exists():  # nothing uploaded yet: an empty list, not an error
            return []
        vector_store = _get_vector_store()
        
        sources = set()
        offset = None
        while True:  # page through the whole collection, not just the first 10k chunks
            records, offset = vector_store.client.scroll(
                collection_name=vector_store.collection_name,
                limit=10000,
                offset=offset,
                with_payload=["metadata.source"],
                with_vectors=False,
            )
            for record in records:
                source = ((record.payload or {}).get("metadata") or {}).get("source")
                if source:
                    sources.add(os.path.basename(source))
            if offset is None:
                break
                    
        sorted_sources = sorted(list(sources))
        logger.info(f"Successfully retrieved {len(sorted_sources)} unique documents.")
        return sorted_sources
        
    except Exception as e:
        logger.exception(f"Error occurred during list_documents: {e}")
        raise RetrievalError(f"Failed to list documents from the vector store: {e}") from e
