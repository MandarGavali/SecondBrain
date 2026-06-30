from fastapi import APIRouter
from secondbrain.graph.workflow import create_graph
from secondbrain.models.requests import ChatRequest
from secondbrain.models.responses import ChatResponse
from secondbrain.core.logger import get_logger
import time

logger = get_logger("api.chat")

router = APIRouter()

# Initialize the new graph (Phase 4)
graph = create_graph()

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    start_time = time.time()
    logger.info(f"Request received. Thread ID: {request.thread_id}, User query: {request.query}")
    
    config = {
        "configurable": {
            "thread_id": str(request.thread_id)  
        }
    }

    # Pass the user query as a message for MessagesState
    result = graph.invoke(
        {
            "messages": [("user", request.query)],
            "user_id": str(request.thread_id)
        },
        config={
            "configurable": {
            "thread_id": str(request.thread_id)  
        }
        }
    )

    # Extract the last message content as the answer
    raw_content = result["messages"][-1].content
    if isinstance(raw_content, list):
        answer = "".join(
            block["text"] 
            for block in raw_content 
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        answer = str(raw_content)
    
    execution_time = time.time() - start_time
    logger.info(f"Request completed in {execution_time:.2f} seconds")

    return ChatResponse(
        answer=answer,
        confidence="High" # Confidence is default High for now
    )