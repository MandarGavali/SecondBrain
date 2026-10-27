import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from secondbrain.api.chat import graph
from secondbrain.api.upload import UPLOAD_DIR
from secondbrain.core.logger import get_logger
from secondbrain.graph.checkpointer import get_checkpointer

logger = get_logger("api.history")

router = APIRouter()

_UUID_PREFIX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_")


def _text(content) -> str:
    """Flatten message content (plain string or list of content blocks) to text."""
    if isinstance(content, list):
        return "".join(
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content or "")


def _visible_messages(thread_id: str):
    """User/assistant turns of a thread, skipping tool calls and tool output."""
    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    messages = []
    for m in state.values.get("messages", []):
        if m.type not in ("human", "ai"):
            continue
        text = _text(m.content).strip()
        if text:
            messages.append({"role": "user" if m.type == "human" else "assistant", "content": text})
    return messages, state.created_at


@router.get("/conversations")
def list_conversations():
    thread_ids = get_checkpointer().checkpoint_collection.distinct("thread_id")
    conversations = []
    for thread_id in thread_ids:
        messages, updated_at = _visible_messages(str(thread_id))
        first_user = next((m["content"] for m in messages if m["role"] == "user"), None)
        if first_user is None:
            continue
        title = " ".join(first_user.split())
        conversations.append({
            "thread_id": str(thread_id),
            "title": title if len(title) <= 60 else title[:57] + "...",
            "updated_at": updated_at,
        })
    conversations.sort(key=lambda c: c["updated_at"] or "", reverse=True)
    return conversations


@router.get("/conversations/{thread_id}")
def get_conversation(thread_id: str):
    messages, _ = _visible_messages(thread_id)
    return {"thread_id": thread_id, "messages": messages}


@router.delete("/conversations/{thread_id}")
def delete_conversation(thread_id: str):
    try:
        get_checkpointer().delete_thread(thread_id)
    except Exception as e:
        logger.exception(f"Failed to delete thread {thread_id}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "deleted"}


@router.get("/documents")
def list_documents():
    documents = []
    for path in UPLOAD_DIR.glob("*.pdf"):
        stat = path.stat()
        documents.append({
            "name": _UUID_PREFIX.sub("", path.name),
            "size": stat.st_size,
            "uploaded_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })
    documents.sort(key=lambda d: d["uploaded_at"], reverse=True)
    return documents
