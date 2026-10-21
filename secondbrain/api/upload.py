import os
import shutil
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from secondbrain.core.logger import get_logger
from secondbrain.queues.jobs import process_pdf

logger = get_logger("api.upload")

router = APIRouter()

# Directory where raw uploaded files are stored (shared with the RQ worker
# through the `shared_data` volume in docker-compose).
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "raw"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _upload_mode() -> str:
    """
    "sync"  -> index the PDF inside the request (default; works on hosts with
               no background worker, e.g. the Render free tier).
    "queue" -> enqueue to Redis/RQ and return a job_id (docker-compose).
    """
    return os.getenv("UPLOAD_MODE", "sync").strip().lower()


def _safe_filename(filename: str | None) -> str:
    """
    Strip any directory components from a client-supplied filename so it
    cannot escape UPLOAD_DIR (e.g. "../../etc/passwd.pdf").
    """
    # Normalise Windows separators too, then keep only the last component.
    name = Path((filename or "").replace("\\", "/")).name
    return name


@router.post("/upload")
def upload_file(file: UploadFile):
    # Plain `def`: FastAPI runs it in a threadpool, so the blocking
    # load -> chunk -> embed -> index work does not stall the event loop.
    start_time = time.time()
    filename = _safe_filename(file.filename)
    logger.info(f"Request received. File: {filename}")

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save the file locally with a unique name
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = UPLOAD_DIR / unique_filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if _upload_mode() == "queue":
        # Imported lazily so the sync deployment never needs Redis.
        from secondbrain.queues.client import queue

        logger.info(f"Queuing PDF for background processing: {unique_filename}")
        job = queue.enqueue(process_pdf, str(file_path))
        logger.info(f"Request completed in {time.time() - start_time:.2f} seconds")
        return {
            "job_id": job.id,
            "status": job.get_status(),
            "message": "PDF queued for processing.",
        }

    logger.info(f"Processing PDF synchronously: {unique_filename}")
    try:
        result = process_pdf(str(file_path))
    except ValueError as e:
        # Bad input (corrupt PDF, no extractable text) -> client error, not 500.
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"PDF processing failed: {e}")
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))

    logger.info(f"Request completed in {time.time() - start_time:.2f} seconds")
    return {
        "status": "completed",
        "message": "PDF processed successfully.",
        "chunks_indexed": result["chunks_indexed"],
    }
