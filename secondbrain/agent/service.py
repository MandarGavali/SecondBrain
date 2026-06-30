from secondbrain.utils.logger import logger
from secondbrain.graph.workflow import create_graph

_graph = None


from secondbrain.rag.pipeline import ingest_document
from pathlib import Path


def upload_document(path: str) -> dict:
    """
    Upload a document into the SecondBrain knowledge base.
    """

    chunks = ingest_document(path)

    return {
        "status": "success",
        "filename": Path(path).name,
        "chunks_indexed": chunks,
    }


def get_graph():
    global _graph

    import time
    from secondbrain.utils.logger import logger
    logger.info(f"[TIMING] get_graph start: {time.perf_counter()}")
    if _graph is None:
        # print("Creating LangGraph...")
        _graph = create_graph()
        logger.info(f"[TIMING] get_graph created: {time.perf_counter()}")

    logger.info(f"[TIMING] get_graph end: {time.perf_counter()}")
    return _graph


def answer_query(
    query: str,
    thread_id: str | None = None,
) -> str:

    import time
    from secondbrain.utils.logger import logger
    logger.info(f"[TIMING] answer_query start: {time.perf_counter()}")

    graph = get_graph()
    logger.info(f"[TIMING] answer_query got graph: {time.perf_counter()}")

    config = {
        "configurable": {
            "thread_id": thread_id or "default"
        }
    }

    logger.info(f"[TIMING] answer_query invoking graph: {time.perf_counter()}")
    # result = graph.invoke(
    #     {
    #         "messages": [("user", query)]
    #     },
    #     config=config
    # )
    try:
        result = graph.invoke(
              {
                "messages": [("user", query)]
            },
            config=config
        )
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            return (
                "Gemini API quota exceeded. "
                "Please try again later or use a different API key."
            )
        raise
    
    logger.info(f"[TIMING] answer_query graph invoked: {time.perf_counter()}")

    logger.info(type(result["messages"][-1].content))
    logger.info(result["messages"][-1].content)

    # If content is a list, convert it to plain text
    content = result["messages"][-1].content

    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )

    return str(content)

# ============================
# Long-Term Memory Services
# ============================

from secondbrain.memory.memory_manager import MemoryManager

_memory_manager = MemoryManager()


def remember(
    text: str,
    user_id: str = "default",
) -> dict:
    """
    Store information into SecondBrain's long-term memory.
    """

    messages = [
        {
            "role": "user",
            "content": text,
        }
    ]

    result = _memory_manager.save_long_term(
        user_id=user_id,
        messages=messages,
    )

    return {
        "status": "success",
        "message": "Memory stored successfully.",
        "result": result,
    }


def list_memories(
    user_id: str = "default",
) -> list:
    """
    Return all stored memories for a user.
    """

    memories = _memory_manager.long_term.get_all_memories(
        user_id=user_id,
    )

    return memories


def forget(
    memory_id: str,
) -> dict:
    """
    Delete a memory from long-term storage.
    """

    result = _memory_manager.long_term.delete_memory(
        memory_id=memory_id,
    )

    return {
        "status": "success",
        "deleted": True,
        "result": result,
    }