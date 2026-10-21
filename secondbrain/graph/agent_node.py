import threading
import time

from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState

from secondbrain.agent.agent import create_agent
from secondbrain.core.logger import get_logger
from secondbrain.memory.memory_manager import MemoryManager

logger = get_logger("graph.agent_node")

_thread_local = threading.local()

_memory_manager: MemoryManager | None = None
_memory_lock = threading.Lock()


def get_agent():
    if not hasattr(_thread_local, "agent"):
        _thread_local.agent = create_agent()
    return _thread_local.agent


def get_memory_manager() -> MemoryManager:
    """
    Lazily create the Mem0-backed MemoryManager.

    Creating it at import time connected to Qdrant as soon as the API module
    was imported, so the app could not even start without the database.
    """
    global _memory_manager
    if _memory_manager is None:
        with _memory_lock:
            if _memory_manager is None:
                _memory_manager = MemoryManager()
    return _memory_manager


def content_to_text(content) -> str:
    """Gemini may return content as a list of parts; flatten it to text."""
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content or "")


def _last_user_message(messages) -> str:
    """
    The most recent *human* message.

    After a tool call the last message in state is a ToolMessage, so using
    messages[-1] searched (and saved) memory with raw tool output.
    """
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return content_to_text(message.content)
    return content_to_text(messages[-1].content) if messages else ""


def agent_node(state: MessagesState):
    logger.debug(f"[TIMING] agent_node start: {time.perf_counter()}")
    messages = state["messages"]
    user_id = state.get("user_id", "default_user")
    last_user_message = _last_user_message(messages)

    # Long-term memory is best-effort: if Mem0/Qdrant is unavailable the
    # assistant should still answer, just without personalised context.
    memory_context = ""
    try:
        memories = get_memory_manager().get_long_term(
            user_id=user_id,
            query=last_user_message,
        )
        memory_context = get_memory_manager().format_memories(memories)
    except Exception as e:
        logger.warning(f"Long-term memory lookup skipped: {e}")

    try:
        agent = get_agent()
        response = agent.invoke(
            {
                "messages": messages,
                "memory_context": memory_context,
            }
        )
    except Exception as e:
        logger.exception(f"Error invoking agent: {e}")
        raise

    # Only persist memory once the agent has produced its final answer.
    # Intermediate turns are tool-call requests with no user-facing text.
    if not getattr(response, "tool_calls", None):
        try:
            get_memory_manager().extract_and_save_memory(
                user_id=user_id,
                user_message=last_user_message,
                assistant_message=content_to_text(response.content),
            )
        except Exception as e:
            logger.warning(f"Long-term memory save skipped: {e}")

    logger.debug(f"[TIMING] agent_node end: {time.perf_counter()}")

    return {
        "messages": [response]
    }
