from secondbrain.core.logger import get_logger
from secondbrain.rag.embeddings.gemini_embeddings import get_embedding_model
from secondbrain.rag.loaders.pdf_loader import load_pdf
from secondbrain.rag.processors.chunker import chunk_documents
from secondbrain.rag.services.retrieval_service import retrieve_relevant_documents
from secondbrain.rag.vectorstore.qdrant_store import create_vector_store

logger = get_logger("rag.pipeline")


def ingest_document(pdf_path: str) -> dict:
    """
    Load -> chunk -> embed -> index a PDF into Qdrant.

    Returns {"chunks_indexed": int, "status": str, "message": str}.
    """
    try:
        # 1. Load the PDF
        logger.info(f"Loading {pdf_path}...")
        try:
            docs = load_pdf(pdf_path)
        except Exception as e:
            # Corrupt / non-PDF content: surface as a client error.
            raise ValueError(f"Could not read PDF: {e}") from e
        
        # 2. Chunk the documents
        chunks = chunk_documents(docs)
        if not chunks:
            # e.g. a scanned/image-only PDF: Qdrant would otherwise fail
            # with an opaque error on an empty batch.
            raise ValueError(
                "No extractable text found in the PDF (is it a scanned image?)."
            )
        
        # 3. Get embeddings
        embedding_model = get_embedding_model()
        
        # 4. Store in Vector Database (Qdrant)
        # Using create_vector_store which calls QdrantVectorStore.from_documents
        create_vector_store(chunks, embedding_model)
        
        return {
            "chunks_indexed": len(chunks),
            "status": "success",
            "message": f"Successfully processed and loaded {len(chunks)} chunks into the vector database."
        }
    except Exception as e:
        logger.exception(f"Error processing {pdf_path}: {e}")
        raise

def answer_query(query: str) -> dict:
    """
    Plain (non-agentic) RAG for debugging the retrieval + generation path:
    User Query -> retrieval_service -> generation_service -> Answer.

    The API and MCP server use the LangGraph agent instead
    (secondbrain.agent.service.answer_query).
    """
    # Imported lazily: the generation service belongs to the legacy
    # corrective-RAG pipeline and is not needed for ingestion.
    from secondbrain.rag.services.generation_service import generate_grounded_answer

    # 1. Retrieve Documents
    search_results = retrieve_relevant_documents(query=query, k=5)

    # 2. Generate Answer
    answer = generate_grounded_answer(query=query, documents=search_results)

    # Pages actually used as context (previously a hard-coded [1, 4, 9, 13]).
    pages = sorted(
        {doc.metadata.get("page_label") for doc in search_results if doc.metadata.get("page_label")},
        key=lambda p: (len(str(p)), str(p)),
    )

    logger.info(f"AI: {answer}")
    return {
        "answer": answer,
        "pages": pages,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    user_query = input("Ask something: ")
    print(answer_query(user_query)["answer"])
