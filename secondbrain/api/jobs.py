import time

from fastapi import APIRouter, HTTPException
from rq.exceptions import NoSuchJobError
from rq.job import Job, JobStatus

from secondbrain.core.logger import get_logger
from secondbrain.queues.client import redis_connection

logger = get_logger("api.jobs")

router = APIRouter()


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    Returns the current status of a background job
    (only used when UPLOAD_MODE=queue).
    """
    start_time = time.time()
    logger.info(f"Request received. Job ID: {job_id}")

    try:
        job = Job.fetch(job_id, connection=redis_connection)
    except NoSuchJobError:
        raise HTTPException(status_code=404, detail="Job not found.")
    except Exception as e:
        # Redis unreachable etc. -- previously reported as "Job not found".
        logger.exception(f"Could not fetch job {job_id}: {e}")
        raise HTTPException(status_code=503, detail="Job queue unavailable.")
    finally:
        logger.info(f"Request completed in {time.time() - start_time:.2f} seconds")

    status = job.get_status()
    response = {"job_id": job.id, "status": status}
    if status == JobStatus.FINISHED:
        response["result"] = job.return_value()
    elif status == JobStatus.FAILED:
        response["error"] = "PDF processing failed. Check the worker logs."
    return response
