import time
from pathlib import Path

from secondbrain.config import settings
from secondbrain.graph.workflow import create_graph
from secondbrain.memory.memory_manager import get_memory_manager
from secondbrain.rag.pipeline import ingest_document
from secondbrain.utils.text import message_text

_graph = None


def upload_document(path: str) -> dict:
    """
    Upload a document into the SecondBrain knowledge base.
    """

    result = ingest_document(path)

    return {
        "status": "success",
        "filename": Path(path).name,
        "chunks_indexed": result["chunks_indexed"],
        "quality": result.get("quality"),
    }


def get_graph():
    global _graph
    if _graph is None:
        _graph = create_graph()
    return _graph


_adaptive_graph = None


def get_adaptive_graph():
    global _adaptive_graph
    if _adaptive_graph is None:
        from secondbrain.graph.adaptive import create_adaptive_graph
        _adaptive_graph = create_adaptive_graph()
    return _adaptive_graph


def run_turn(query: str, thread_id=None, user_id: str | None = None) -> dict:
    """Single entry point for one chat turn. Returns a dict matching ChatResponse (minus `reflection`)."""
    started = time.perf_counter()
    tid = str(thread_id) if thread_id is not None else "default"
    uid = str(user_id) if user_id else tid          # same default as the old API: user_id == thread_id
    config = {"configurable": {"thread_id": tid}, "recursion_limit": 30}

    if settings.graph_mode == "adaptive":
        from secondbrain.graph.adaptive import new_turn_input
        from secondbrain.rag.evidence import build_sources

        result = get_adaptive_graph().invoke(new_turn_input(query, uid), config=config)
        answer = result.get("answer") or message_text(result["messages"][-1].content)
        metrics = dict(result.get("metrics") or {})
        metrics["latency_ms"] = int((time.perf_counter() - started) * 1000)
        metrics["route_method"] = result.get("route_method")
        metrics["retries"] = result.get("retries", 0)
        label = result.get("confidence_label")
        if label is None and settings.enable_verify and result.get("route") == "no_search":
            label = "N/A"  # verify never runs on the chat route: no document evidence was used
        return {
            "answer": answer,
            "confidence": label or "Unverified",
            "confidence_score": result.get("confidence_score"),
            "route": result.get("route"),
            "grounded": result.get("is_grounded"),
            "abstained": bool(result.get("abstained")),
            "needs_review": bool(result.get("needs_review")),
            "sources": build_sources(result.get("evidence") or []),
            "metrics": metrics,
        }

    # legacy graph (GRAPH_MODE=agent)
    result = get_graph().invoke({"messages": [("user", query)], "user_id": uid}, config=config)
    return {
        "answer": message_text(result["messages"][-1].content),
        "confidence": "Unverified",
        "confidence_score": None, "route": None, "grounded": None,
        "abstained": False, "needs_review": False, "sources": [],
        "metrics": {"latency_ms": int((time.perf_counter() - started) * 1000)},
    }


def answer_query(query: str, thread_id: str | None = None, user_id: str | None = None) -> str:
    """Kept for the MCP `ask_secondbrain` tool (returns text only)."""
    try:
        return run_turn(query, thread_id or "default", user_id)["answer"]
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            return "Gemini API quota exceeded. Please try again later or use a different API key."
        raise


def end_session(thread_id, user_id: str | None = None, background_tasks=None) -> dict:
    """Signal that a conversation is over -> AAM reflection runs in the background."""
    if not settings.enable_aam:
        return {"status": "skipped", "reason": "ENABLE_AAM=0"}
    from secondbrain.memory.reflection import build_transcript, schedule_reflection

    tid = str(thread_id)
    uid = str(user_id) if user_id else tid
    graph = get_adaptive_graph() if settings.graph_mode == "adaptive" else get_graph()
    snapshot = graph.get_state({"configurable": {"thread_id": tid}})
    messages = (snapshot.values or {}).get("messages", []) if snapshot else []
    return schedule_reflection(uid, build_transcript(messages), background_tasks)

# ============================
# Long-Term Memory Services
# ============================


def remember(text: str, user_id: str = "default") -> dict:
    """Store information into SecondBrain's long-term memory."""
    result = get_memory_manager().save_long_term(
        user_id=user_id, messages=[{"role": "user", "content": text}]
    )
    return {"status": "success", "message": "Memory stored successfully.", "result": result}


def list_memories(user_id: str = "default") -> dict:
    """Return the user's active memories (AAM-deprecated ones are hidden, as on recall)."""
    from secondbrain.memory.reflection import filter_active

    return filter_active(get_memory_manager().long_term.get_all_memories(user_id=user_id), user_id)


def forget(memory_id: str) -> dict:
    """Delete a memory from long-term storage (and its AAM status row, if any)."""
    from secondbrain.memory.status_store import get_status_store

    result = get_memory_manager().long_term.delete_memory(memory_id=memory_id)
    get_status_store().remove(memory_id)
    return {"status": "success", "deleted": True, "result": result}
