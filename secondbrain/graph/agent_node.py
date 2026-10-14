import threading

from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState

from secondbrain.agent.agent import create_agent
from secondbrain.core.logger import get_logger
from secondbrain.memory.memory_manager import get_memory_manager
from secondbrain.utils.text import message_text

logger = get_logger("graph.agent_node")

_thread_local = threading.local()


def get_agent():
    if not hasattr(_thread_local, "agent"):
        _thread_local.agent = create_agent()
    return _thread_local.agent


def agent_node(state: MessagesState):
    """Legacy agent step: recall memory, call the tool-calling agent, save the turn to memory."""
    messages = state["messages"]
    user_id = state.get("user_id", "default_user")
    # After a tool call the last message is a ToolMessage, so look for the user's own message.
    last_user_message = next(
        (message_text(m.content) for m in reversed(messages) if isinstance(m, HumanMessage)), ""
    )

    memory_manager = get_memory_manager()
    memories = memory_manager.get_long_term(user_id=user_id, query=last_user_message)
    memory_context = memory_manager.format_memories(memories)

    try:
        response = get_agent().invoke({"messages": messages, "memory_context": memory_context})
    except Exception as e:
        logger.exception(f"Error invoking agent: {e}")
        raise

    if not response.tool_calls:  # save once per turn, when the agent gives its final answer
        memory_manager.extract_and_save_memory(
            user_id=user_id,
            user_message=last_user_message,
            assistant_message=message_text(response.content),
        )

    return {"messages": [response]}
