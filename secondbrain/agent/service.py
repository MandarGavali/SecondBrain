"""
Service layer shared by the REST API, the CLI and the MCP server.

All callers go through one lazily-compiled LangGraph instance.
"""

import threading
from pathlib import Path

from secondbrain.core.logger import get_logger
from secondbrain.graph.agent_node import content_to_text, get_memory_manager
from secondbrain.graph.workflow import create_graph
from secondbrain.rag.pipeline import ingest_document

logger = get_logger("agent.service")

_graph = None
_graph_lock = threading.Lock()


def upload_document(path: str) -> dict:
    """
    Upload a document into the SecondBrain knowledge base.
    """

    result = ingest_document(path)

    return {
        "status": "success",
        "filename": Path(path).name,
        "chunks_indexed": result["chunks_indexed"],
    }


def get_graph():
    global _graph
    if _graph is None:
        with _graph_lock:
            if _graph is None:
                logger.info("Compiling LangGraph workflow")
                _graph = create_graph()
    return _graph


def answer_query(
    query: str,
    thread_id: str | None = None,
    user_id: str | None = None,
) -> str:
    """
    Run one conversational turn through the agent graph.

    thread_id scopes short-term memory (MongoDB checkpoints); user_id scopes
    long-term memory (Mem0).  user_id defaults to thread_id.
    """
    thread_id = thread_id or "default"
    graph = get_graph()

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    try:
        result = graph.invoke(
            {
                "messages": [("user", query)],
                "user_id": user_id or thread_id,
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

    return content_to_text(result["messages"][-1].content)

# ============================
# Long-Term Memory Services
# ============================


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

    result = get_memory_manager().save_long_term(
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

    memories = get_memory_manager().long_term.get_all_memories(
        user_id=user_id,
    )

    return memories


def forget(
    memory_id: str,
) -> dict:
    """
    Delete a memory from long-term storage.
    """

    result = get_memory_manager().long_term.delete_memory(
        memory_id=memory_id,
    )

    return {
        "status": "success",
        "deleted": True,
        "result": result,
    }
