# from typing import List
# from langchain_core.documents import Document
# from langchain_qdrant import QdrantVectorStore

# def retrieve_documents(query: str, vector_store: QdrantVectorStore, k: int = 5) -> List[Document]:
#     """Retrieves documents using the vector store as a retriever."""
#     retriever = vector_store.as_retriever(search_kwargs={"k": k})
#     search_results = retriever.invoke(query)
#     return search_results

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