from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from secondbrain.graph.workflow import create_graph
from secondbrain.models.requests import ChatRequest
from secondbrain.models.responses import ChatResponse
from secondbrain.core.logger import get_logger
import json
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


TOOL_STATUS = {
    "search_documents": "Searching your documents",
    "summarize_documents": "Summarizing your documents",
    "list_documents": "Looking through your documents",
    "generate_questions": "Writing questions",
}


def _message_text(content) -> str:
    if isinstance(content, list):
        return "".join(
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    """
    Same as /chat, but streams newline-delimited JSON events so the UI can
    show what the agent is doing: {"type": "status" | "answer" | "error", ...}
    """
    logger.info(f"Stream request received. Thread ID: {request.thread_id}, User query: {request.query}")

    def events():
        yield json.dumps({"type": "status", "text": "Thinking"}) + "\n"
        try:
            answer = ""
            after_tools = False
            for mode, chunk in graph.stream(
                {"messages": [("user", request.query)], "user_id": str(request.thread_id)},
                config={"configurable": {"thread_id": str(request.thread_id)}},
                stream_mode=["updates", "custom"],
            ):
                if mode == "custom":
                    text = chunk.get("status", "")
                    if text == "Thinking" and after_tools:
                        text = "Writing the answer"
                    yield json.dumps({"type": "status", "text": text}) + "\n"
                    continue
                for node, data in chunk.items():
                    messages = (data or {}).get("messages") or []
                    if node == "agent" and messages:
                        last = messages[-1]
                        tool_calls = getattr(last, "tool_calls", None)
                        if tool_calls:
                            text = TOOL_STATUS.get(tool_calls[0]["name"], f"Using {tool_calls[0]['name']}")
                            yield json.dumps({"type": "status", "text": text}) + "\n"
                        else:
                            answer = _message_text(last.content)
                    elif node == "tools":
                        after_tools = True
            yield json.dumps({"type": "answer", "answer": answer, "confidence": "High"}) + "\n"
        except Exception as e:
            logger.exception("Streaming chat failed")
            message = str(e)
            if "RESOURCE_EXHAUSTED" in message or "429" in message:
                message = "The Gemini API quota is exhausted (free tier limit). Try again later or use a different API key."
            yield json.dumps({"type": "error", "message": message}) + "\n"

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )