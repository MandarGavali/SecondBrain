from secondbrain.core.logger import get_logger
logger = get_logger("graph.agent_node")
from langgraph.graph import MessagesState
from secondbrain.agent.agent import create_agent
from secondbrain.memory.memory_manager import MemoryManager

import threading

_thread_local = threading.local()

def get_agent():
    if not hasattr(_thread_local, "agent"):
        _thread_local.agent = create_agent()
    return _thread_local.agent

memory_manager = MemoryManager()


def agent_node(state: MessagesState):

    import time
    from secondbrain.utils.logger import logger
    logger.info(f"[TIMING] agent_node start: {time.perf_counter()}")
    messages = state["messages"]
    user_id = state.get("user_id", "default_user")
    last_user_message = messages[-1].content

    logger.info(f"[TIMING] getting long-term memory start: {time.perf_counter()}")
    memories = memory_manager.get_long_term(
        user_id=user_id,
        query=last_user_message,
    )
    logger.info(f"[TIMING] getting long-term memory end: {time.perf_counter()}")

    memory_context = memory_manager.format_memories(memories)


    # logger.info("[DEBUG] Invoking agent...")
    #logger.info("========== BEFORE AGENT.INVOKE ==========")

    # logger.info("Messages:", messages)
    # logger.info("Memory Context:", memory_context)

    try:
        logger.info(f"[TIMING] agent.invoke start: {time.perf_counter()}")
        agent = get_agent()
        response = agent.invoke(
            {
                "messages": messages,
                "memory_context": memory_context,
            }
        )
        logger.info(f"[TIMING] agent.invoke end: {time.perf_counter()}")

    except Exception as e:
        logger.exception(f"Error invoking agent: {e}")
        raise 

    logger.info(f"[TIMING] extract_and_save_memory start: {time.perf_counter()}")
    memory_manager.extract_and_save_memory(
        user_id=user_id,
        user_message=last_user_message,
        assistant_message=response.content,
    )
    logger.info(f"[TIMING] agent_node end: {time.perf_counter()}")

    return {
        "messages": [response]
    }