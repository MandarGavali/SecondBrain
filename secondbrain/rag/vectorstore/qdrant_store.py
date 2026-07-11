import os
from secondbrain.utils.logger import logger
from typing import List
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "Learning_RAG"

def create_vector_store(chunks: List[Document], embedding_model: GoogleGenerativeAIEmbeddings) -> QdrantVectorStore:
    """Creates a new vector store and indexes chunks."""
    vector_store = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embedding_model,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME
    )
    # logger.info("Indexing complete [OK]")
    return vector_store

def get_existing_vector_store(embedding_model: GoogleGenerativeAIEmbeddings) -> QdrantVectorStore:
    """Loads an existing Qdrant vector store collection."""
    vector_store = QdrantVectorStore.from_existing_collection(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME,
        embedding=embedding_model
    )
    return vector_store
