from fastapi import APIRouter, BackgroundTasks

from secondbrain.agent.service import end_session, run_turn
from secondbrain.core.logger import get_logger
from secondbrain.models.requests import ChatRequest
from secondbrain.models.responses import ChatResponse

logger = get_logger("api.chat")
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    logger.info(f"Chat request. thread={request.thread_id} query={request.query!r}")
    result = run_turn(request.query, request.thread_id, request.user_id)

    reflection = None
    if request.session_end:
        reflection = end_session(request.thread_id, request.user_id, background_tasks)

    logger.info(f"Chat done. route={result.get('route')} latency_ms={result['metrics'].get('latency_ms')}")
    return ChatResponse(**result, reflection=reflection)
