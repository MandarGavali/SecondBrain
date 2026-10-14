from typing import List, Tuple

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore

from secondbrain.core.logger import get_logger

logger = get_logger("rag.retriever")


def retrieve_documents(query: str, vector_store: QdrantVectorStore, k: int = 5) -> List[Document]:
    results = vector_store.similarity_search_with_score(query, k=k)

    logger.info(f"Retrieved {len(results)} results")
    for i, (doc, score) in enumerate(results):
        logger.info(f"Result {i + 1} | Score: {score}")
        logger.info(f"Metadata: {doc.metadata}")
        logger.info(f"Content: {doc.page_content[:200]}")

    return [doc for doc, _ in results]


def retrieve_documents_with_scores(
    query: str, vector_store: QdrantVectorStore, k: int = 5
) -> List[Tuple[Document, float]]:
    """Same as retrieve_documents but keeps the similarity score (cosine, higher = closer)."""
    results = vector_store.similarity_search_with_score(query, k=k)
    return [(doc, float(score)) for doc, score in results]
