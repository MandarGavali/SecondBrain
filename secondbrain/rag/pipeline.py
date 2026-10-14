from secondbrain.config import settings
from secondbrain.core.logger import get_logger
from secondbrain.rag.embeddings.gemini_embeddings import get_embedding_model
from secondbrain.rag.loaders.pdf_loader import load_pdf
from secondbrain.rag.processors.chunker import chunk_documents
from secondbrain.rag.processors.quality_filter import filter_chunks
from secondbrain.rag.vectorstore.qdrant_store import create_vector_store

logger = get_logger("rag.pipeline")


def ingest_document(pdf_path: str) -> dict:
    """PDF -> pages -> chunks -> quality filter (P4 stage 1) -> embeddings -> Qdrant."""
    try:
        logger.info(f"Loading {pdf_path}...")
        chunks = chunk_documents(load_pdf(pdf_path))

        quality = None
        if settings.quality_enabled:
            chunks, quality = filter_chunks(chunks)
            logger.info(f"Quality filter: {quality}")
        if not chunks:
            raise ValueError("No usable text found in the document (empty or scanned PDF?).")

        create_vector_store(chunks, get_embedding_model())

        return {
            "chunks_indexed": len(chunks),
            "status": "success",
            "quality": quality,
            "message": f"Successfully processed and loaded {len(chunks)} chunks into the vector database.",
        }
    except Exception as e:
        logger.exception(f"Error processing {pdf_path}: {e}")
        raise
