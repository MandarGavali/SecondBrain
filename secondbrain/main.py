from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from secondbrain.core.exceptions import SecondBrainError
from secondbrain.core.logger import get_logger

logger = get_logger("main")

from secondbrain.api.chat import router as chat_router
from secondbrain.api.upload import router as upload_router
from secondbrain.api.jobs import router as jobs_router

app = FastAPI(
    title="SecondBrain AI"
)

app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(jobs_router)

@app.exception_handler(SecondBrainError)
async def secondbrain_exception_handler(request: Request, exc: SecondBrainError):
    logger.error(f"SecondBrainError caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc)
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (StarletteHTTPException, RequestValidationError)):
        raise exc
    logger.exception("Unexpected error caught globally")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred."
            }
        }
    )