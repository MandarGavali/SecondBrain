from secondbrain.utils.logger import logger
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, HTTPException
import uuid

from secondbrain.queues.client import queue
from secondbrain.queues.jobs import process_pdf
from secondbrain.core.logger import get_logger
import time

logger = get_logger("api.upload")

router = APIRouter()

# Define the directory to save raw uploaded files
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "raw"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile):
    start_time = time.time()
    logger.info(f"Request received. User query/file: {file.filename}")
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    #save the file locally with a unique name
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logger.info(f"📤 Queuing PDF for background processing: {unique_filename}")
   
    job = queue.enqueue(
    process_pdf,
    str(file_path)
    )
    
    execution_time = time.time() - start_time
    logger.info(f"Request completed in {execution_time:.2f} seconds")

    return {
        "job_id": job.id,
        "status": job.get_status(),
        "message": "PDF queued for processing."
    }
