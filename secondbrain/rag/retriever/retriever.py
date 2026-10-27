from typing import List
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore

from secondbrain.core.logger import get_logger

logger = get_logger("rag.retriever")

def retrieve_documents(query: str, vector_store: QdrantVectorStore, k: int = 5) -> List[Document]:
    results = vector_store.similarity_search_with_score(query, k=k)

    logger.info(f"Retrieved {len(results)} results")

    for i, (doc, score) in enumerate(results):
        logger.info(f"Result {i+1} | Score: {score}")
        logger.info(f"Metadata: {doc.metadata}")
        logger.info(f"Content: {doc.page_content[:200]}")

    return [doc for doc, score in results]