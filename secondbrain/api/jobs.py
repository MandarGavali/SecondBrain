from fastapi import APIRouter, HTTPException
from rq.job import Job

from secondbrain.queues.client import redis_connection
from secondbrain.core.logger import get_logger
import time

logger = get_logger("api.jobs")

router = APIRouter()


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    Returns the current status of a background job.
    """
    start_time = time.time()
    logger.info(f"Request received. User query/job_id: {job_id}")

    try:
        job = Job.fetch(
            job_id,
            connection=redis_connection
        )

        return {
            "job_id": job.id,
            "status": job.get_status()
        }
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )
    finally:
        execution_time = time.time() - start_time
        logger.info(f"Request completed in {execution_time:.2f} seconds")