import json
import re
import threading
from datetime import datetime, timezone

from langchain_core.messages import AIMessage, HumanMessage

from secondbrain.config import settings
from secondbrain.core.logger import get_logger
from secondbrain.utils.text import message_text

logger = get_logger("memory.reflection")

_EXTRACT_PROMPT = """Today is {today}.
From the conversation below, extract durable facts about the USER (role, preferences, decisions,
project details, schedules, constraints). Ignore questions, small talk and facts about documents.
Write each fact as one short, self-contained sentence. Return ONLY a JSON array of strings
(at most {max_facts}); return [] if there is nothing worth remembering.

Conversation:
{transcript}
"""

_JUDGE_PROMPT = """New fact: {fact}

Existing memories:
{numbered}

For each existing memory decide how it relates to the new fact:
- SAME: says the same thing
- CONTRADICTS: cannot both be true now (the new fact replaces it)
- UNRELATED: different topic or compatible
Return ONLY a JSON object mapping the memory number to a label, e.g. {{"1": "CONTRADICTS", "2": "UNRELATED"}}.
"""


def _default_llm_call(prompt: str) -> str:
    from secondbrain.rag.llm.gemini_llm import get_llm

    return message_text(get_llm().invoke(prompt).content)


def build_transcript(messages: list, max_messages: int = 40) -> list[dict]:
    """LangChain messages -> [{'role','content'}] (human/assistant text only)."""
    out: list[dict] = []
    for m in messages or []:
        if isinstance(m, HumanMessage):
            text = message_text(m.content).strip()
            if text:
                out.append({"role": "user", "content": text})
        elif isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
            text = message_text(m.content).strip()
            if text:
                out.append({"role": "assistant", "content": text})
    return out[-max_messages:]


def _parse_json(text: str, opener: str, closer: str):
    match = re.search(re.escape(opener) + r".*" + re.escape(closer), text or "", re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def extract_facts(transcript: list[dict], llm_call=None) -> list[str]:
    llm_call = llm_call or _default_llm_call
    text = "\n".join(f"{t['role'].capitalize()}: {t['content']}" for t in transcript)[-6000:]
    prompt = _EXTRACT_PROMPT.format(
        today=datetime.now(timezone.utc).date().isoformat(),
        max_facts=settings.aam_max_facts,
        transcript=text,
    )
    data = _parse_json(llm_call(prompt), "[", "]")
    if not isinstance(data, list):
        return []
    facts = [f.strip() for f in data if isinstance(f, str) and f.strip()]
    return facts[: settings.aam_max_facts]


def judge_conflicts(fact: str, candidates: list[dict], llm_call=None) -> dict[int, str]:
    """Return {candidate_index (0-based): 'SAME'|'CONTRADICTS'|'UNRELATED'}. Parse failure -> {}."""
    llm_call = llm_call or _default_llm_call
    numbered = "\n".join(f"{i + 1}. {c.get('memory', '')}" for i, c in enumerate(candidates))
    data = _parse_json(llm_call(_JUDGE_PROMPT.format(fact=fact, numbered=numbered)), "{", "}")
    labels: dict[int, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            try:
                idx = int(key) - 1
            except (TypeError, ValueError):
                continue
            label = str(value).strip().upper()
            if 0 <= idx < len(candidates) and label in {"SAME", "CONTRADICTS", "UNRELATED"}:
                labels[idx] = label
    return labels


def reflect_session(user_id: str, transcript: list[dict], *, memory=None, store=None, llm_call=None) -> dict:
    """Background job. Extract facts, detect conflicts, deprecate stale memories, store new facts.

    memory: object with search_memory(user_id, query, limit) and save_memory(user_id, messages, metadata, infer)
    store : MemoryStatusStore-like (deprecated_ids, deprecate)
    """
    if memory is None:
        from secondbrain.memory.memory_manager import get_memory_manager

        memory = get_memory_manager().long_term
    if store is None:
        from secondbrain.memory.status_store import get_status_store

        store = get_status_store()

    stats = {"facts": 0, "added": 0, "skipped_same": 0, "deprecated": 0}
    facts = extract_facts(transcript, llm_call)
    stats["facts"] = len(facts)
    deprecated = store.deprecated_ids(user_id)

    for fact in facts:
        found = memory.search_memory(user_id=user_id, query=fact, limit=5)
        items = found.get("results", []) if isinstance(found, dict) else (found or [])
        candidates = [
            m for m in items
            if m.get("id") not in deprecated
            and (m.get("score") is None or m["score"] >= settings.aam_sim_threshold)
        ]
        labels = judge_conflicts(fact, candidates, llm_call) if candidates else {}
        contradicted = [candidates[i] for i, lab in labels.items() if lab == "CONTRADICTS"]
        if any(lab == "SAME" for lab in labels.values()) and not contradicted:
            stats["skipped_same"] += 1
            continue

        saved = memory.save_memory(
            user_id=user_id,
            messages=[{"role": "user", "content": fact}],
            metadata={"status": "active", "source": "aam",
                      "created_at": datetime.now(timezone.utc).isoformat()},
            infer=False,
        )
        results = saved.get("results", []) if isinstance(saved, dict) else []
        new_id = results[0].get("id") if results else None
        stats["added"] += 1

        for old in contradicted:
            store.deprecate(
                memory_id=old["id"], user_id=user_id, old_text=old.get("memory"),
                superseded_by=new_id, new_text=fact, reason="contradiction",
            )
            deprecated.add(old["id"])
            stats["deprecated"] += 1

    logger.info(f"AAM reflection for user={user_id}: {stats}")
    return stats


def _safe_reflect(user_id: str, transcript: list[dict]) -> None:
    try:
        reflect_session(user_id, transcript)
    except Exception:
        logger.exception("AAM reflection failed")


def schedule_reflection(user_id: str, transcript: list[dict], background_tasks=None) -> dict:
    if not transcript:
        return {"status": "skipped", "reason": "empty transcript"}
    mode = (settings.aam_mode or "background").lower()
    if mode == "queue":
        from secondbrain.queues.client import queue
        from secondbrain.queues.jobs import reflect_session_job

        job = queue.enqueue(reflect_session_job, user_id, transcript)
        return {"status": "queued", "job_id": job.id}
    if mode == "inline":
        return {"status": "done", "stats": reflect_session(user_id, transcript)}
    if background_tasks is not None:
        background_tasks.add_task(_safe_reflect, user_id, transcript)
    else:
        threading.Thread(target=_safe_reflect, args=(user_id, transcript), daemon=True).start()
    return {"status": "scheduled"}


def filter_active(memories, user_id: str) -> dict:
    """Drop deprecated memories from a Mem0 search result (dict with 'results' or a list)."""
    items = memories.get("results", []) if isinstance(memories, dict) else (memories or [])
    if not settings.enable_aam:
        return {"results": items}
    from secondbrain.memory.status_store import get_status_store

    dead = get_status_store().deprecated_ids(user_id)
    return {"results": [m for m in items if m.get("id") not in dead]}
