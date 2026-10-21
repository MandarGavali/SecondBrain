from typing import List

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore

from secondbrain.core.logger import get_logger

logger = get_logger("rag.retriever")


def retrieve_documents(query: str, vector_store: QdrantVectorStore, k: int = 5) -> List[Document]:
    """Return the top-k chunks for ``query`` and log their similarity scores."""
    results = vector_store.similarity_search_with_score(query, k=k)

    logger.info(f"Retrieved {len(results)} results")

    # Per-chunk details are DEBUG-level: they include document text, which
    # should not end up in production logs by default.
    for i, (doc, score) in enumerate(results):
        logger.debug(f"Result {i+1} | Score: {score}")
        logger.debug(f"Metadata: {doc.metadata}")
        logger.debug(f"Content: {doc.page_content[:200]}")

    return [doc for doc, score in results]
