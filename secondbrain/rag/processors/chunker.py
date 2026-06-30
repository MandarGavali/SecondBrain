from secondbrain.utils.logger import logger
from typing import List
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_documents(documents: List[Document]) -> List[Document]:
    """Splits documents into chunks and enriches metadata."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents=documents)
    
    # Enrich metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"chunk_{i}"
        # Extract document name from 'source' if available
        source = chunk.metadata.get("source", "unknown")
        chunk.metadata["document_name"] = Path(source).name
        # Note: 'source' and 'page_label' are preserved automatically by langchain
        
    logger.info(f"Split into {len(chunks)} chunks.")
    return chunks
