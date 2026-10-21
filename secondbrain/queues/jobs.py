from secondbrain.core.logger import get_logger
from secondbrain.rag.pipeline import ingest_document

logger = get_logger("queues.jobs")


def process_pdf(pdf_path: str) -> dict:
    """
    Process and index a PDF.

    Runs inside the RQ worker (UPLOAD_MODE=queue) or directly inside the
    /upload request (UPLOAD_MODE=sync).  Returns the ingestion result dict
    ({"chunks_indexed", "status", "message"}).
    """
    logger.info("=" * 60)
    logger.info("PDF Processing Started")
    logger.info(f"File: {pdf_path}")

    try:
        result = ingest_document(pdf_path)

        logger.info(f"Successfully indexed {result['chunks_indexed']} chunks.")
        logger.info("=" * 60)

        return result

    except Exception as e:
        logger.info("=" * 60)
        logger.info("PDF Processing Failed")
        logger.info(f"File: {pdf_path}")
        logger.exception(f"Error: {e}")
        logger.info("=" * 60)

        # Re-raise so RQ marks the job as failed
        raise
