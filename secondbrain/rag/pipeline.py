from secondbrain.core.logger import get_logger
logger = get_logger("rag.pipeline")
import sys
from pathlib import Path

# Ensure the rag module is in the Python path

from secondbrain.rag.services.retrieval_service import retrieve_relevant_documents
from secondbrain.rag.services.generation_service import generate_grounded_answer

from secondbrain.rag.loaders.pdf_loader import load_pdf
from secondbrain.rag.processors.chunker import chunk_documents
from secondbrain.rag.embeddings.gemini_embeddings import get_embedding_model
from secondbrain.rag.vectorstore.qdrant_store import create_vector_store

def ingest_document(pdf_path: str):
    # if not file.filename.endswith(".pdf"):
    #     raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # 1. Save the file locally
    # file_path = UPLOAD_DIR / file.filename
    # with open(file_path, "wb") as buffer:
    #     shutil.copyfileobj(file.file, buffer)
        
    try:
        # 2. Load the PDF
        logger.info(f"Loading {pdf_path}...")
        docs = load_pdf(pdf_path)
        
        # 3. Chunk the documents
        chunks = chunk_documents(docs)
        
        # 4. Get embeddings
        embedding_model = get_embedding_model()
        
        # 5. Store in Vector Database (Qdrant)
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

def answer_query(query: str):
    """
    Orchestrates the entire RAG flow:
    User Query -> retrieval_service -> generation_service -> Return Answer
    """
    # 1. Retrieve Documents
    search_results = retrieve_relevant_documents(query=query, k=5)

    # Debug Retrieval
    for i, doc in enumerate(search_results):
        logger.info("=" * 50)
        logger.info(f"Chunk {i}")
        logger.info(doc.metadata)
        logger.info(doc.page_content[:500])

    # 2. Generate Answer
    answer = generate_grounded_answer(query=query, documents=search_results)
    
    logger.info(f"AI🤖 : {answer}")
    return {
        "answer": answer,
        "confidence": "High",
        "pages": [1,4,9,13]
    }



 

if __name__ == "__main__":
    user_query = input("Ask something: ")
    answer_query(user_query)


