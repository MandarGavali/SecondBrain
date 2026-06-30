from typing import List
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore

def retrieve_documents(query: str, vector_store: QdrantVectorStore, k: int = 5) -> List[Document]:
    """Retrieves documents using the vector store as a retriever."""
    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    search_results = retriever.invoke(query)
    return search_results

