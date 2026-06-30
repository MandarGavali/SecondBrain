import os
from typing import List

from secondbrain.rag.services.retrieval_service import _get_vector_store
from secondbrain.utils.exceptions import RetrievalError
from secondbrain.utils.logger import logger

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
        vector_store = _get_vector_store()
        
        # Scroll through the collection to extract metadata payload
        records, _ = vector_store.client.scroll(
            collection_name=vector_store.collection_name,
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        
        sources = set()
        for record in records:
            if record.payload and "metadata" in record.payload:
                source = record.payload["metadata"].get("source")
                if source:
                    # Extract just the filename (basename) from the full path
                    sources.add(os.path.basename(source))
                    
        sorted_sources = sorted(list(sources))
        logger.info(f"Successfully retrieved {len(sorted_sources)} unique documents.")
        return sorted_sources
        
    except Exception as e:
        logger.exception(f"Error occurred during list_documents: {e}")
        raise RetrievalError(f"Failed to list documents from the vector store: {e}") from e
