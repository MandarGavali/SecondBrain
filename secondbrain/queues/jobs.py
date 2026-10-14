from secondbrain.core.logger import get_logger
logger = get_logger("queues.jobs")
from secondbrain.rag.pipeline import ingest_document


def process_pdf(pdf_path: str):
    """
    Background job responsible for processing and indexing a PDF.

    This function is executed by the RQ worker.
    """

    logger.info("=" * 60)
    logger.info("Background PDF Processing Started")
    logger.info(f"File: {pdf_path}")

    try:
        # Call the RAG ingestion pipeline
        result = ingest_document(pdf_path)

        logger.info(f"Successfully indexed {result['chunks_indexed']} chunks.")
        logger.info("=" * 60)

        return result

    except Exception as e:
        logger.info("=" * 60)
        logger.info("Background PDF Processing Failed")
        logger.info(f"File: {pdf_path}")
        logger.exception(f"Error: {e}")
        logger.info("=" * 60)

        # Re-raise so RQ marks the job as failed
        raise


def reflect_session_job(user_id: str, transcript: list):
    """RQ job: AAM reflection after a conversation ends."""
    from secondbrain.memory.reflection import reflect_session

    logger.info(f"AAM job started for user={user_id}")
    return reflect_session(user_id, transcript)
