import shutil
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from secondbrain.core.logger import get_logger
from secondbrain.queues.jobs import process_pdf

logger = get_logger("api.upload")

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "raw"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
def upload_file(file: UploadFile):
    """Index a PDF synchronously (Render's free tier has no background workers).

    A sync handler runs in FastAPI's threadpool, so a long ingestion does not block other requests.
    """
    start_time = time.time()
    filename = Path(file.filename or "").name  # drop any client-supplied directories
    logger.info(f"Upload received: {filename}")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = UPLOAD_DIR / unique_filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = process_pdf(str(file_path))
    except Exception as e:
        logger.exception(f"PDF processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    logger.info(f"Upload processed in {time.time() - start_time:.2f} seconds")
    return {
        "status": "completed",
        "message": "PDF processed successfully.",
        "document": unique_filename,
        "chunks_indexed": result.get("chunks_indexed"),
        "quality": result.get("quality"),
    }
