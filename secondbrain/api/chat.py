import time

from fastapi import APIRouter

from secondbrain.agent.service import answer_query
from secondbrain.core.logger import get_logger
from secondbrain.models.requests import ChatRequest
from secondbrain.models.responses import ChatResponse

logger = get_logger("api.chat")

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    start_time = time.time()
    thread_id = str(request.thread_id)
    logger.info(f"Request received. Thread ID: {thread_id}")

    # Shares the single lazily-compiled graph with the CLI and MCP server
    # (previously compiled at import time, which needed MongoDB to be up
    # before the app could even start).
    answer = answer_query(
        query=request.query,
        thread_id=thread_id,
        user_id=thread_id,
    )

    logger.info(f"Request completed in {time.time() - start_time:.2f} seconds")

    return ChatResponse(
        answer=answer,
        confidence="High"  # Placeholder: no confidence scoring yet
    )
