"""Read-mostly endpoints behind the web UI's inspector views: config, router and LO-MCP playgrounds, memory."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from secondbrain.config import _DEFS, settings
from secondbrain.core.logger import get_logger

logger = get_logger("api.insights")
router = APIRouter()

# UI grouping of the flags in config.py (anything not listed lands in "other")
_GROUPS = {
    "Orchestration": ["graph_mode", "force_route", "max_agent_steps", "simple_k", "retry_k"],
    "P1 · Adaptive router": ["enable_router", "router_mode"],
    "P2 · LO-MCP tool selection": ["enable_lomcp", "lomcp_top_k", "lomcp_margin", "lomcp_min_sim",
                                   "lomcp_always_include"],
    "P3 · Adaptive memory (AAM)": ["enable_aam", "aam_mode", "aam_sim_threshold", "aam_max_facts"],
    "P4 · Verification": ["enable_verify", "verify_simple_llm", "w_retrieval", "w_relevance", "w_grounded",
                          "score_rel_min", "conf_high", "conf_medium", "conf_abstain", "max_retries"],
    "Ingestion quality": ["quality_enabled", "quality_min_chars", "quality_min_alpha"],
}


class QueryIn(BaseModel):
    query: str


class MemoryIn(BaseModel):
    text: str
    user_id: str = "default"


def _quota_safe(fn):
    try:
        return fn()
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(status_code=503, detail="Gemini API quota exceeded. Please try again later.")
        logger.exception("insights call failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system")
def system():
    """Every feature flag and threshold with its current value, grouped by research extension."""
    grouped = {name: [] for name in _GROUPS}
    grouped["Other"] = []
    for attr, (env, typ, default) in _DEFS.items():
        group = next((g for g, attrs in _GROUPS.items() if attr in attrs), "Other")
        grouped[group].append({
            "name": attr, "env": env, "type": typ.__name__,
            "value": getattr(settings, attr), "default": default,
        })
    return {"graph_mode": settings.graph_mode, "groups": {g: v for g, v in grouped.items() if v}}


@router.post("/route")
def route(body: QueryIn):
    """P1 playground: how the router would classify a query (heuristics first, Gemini if unsure)."""
    from secondbrain.routing.classifier import classify_query, heuristic_classify

    heuristic_label, heuristic_reason = heuristic_classify(body.query)
    result = _quota_safe(lambda: classify_query(body.query))
    return {**result, "heuristic": {"label": heuristic_label, "reason": heuristic_reason}}


@router.post("/tools/predict")
def tools_predict(body: QueryIn):
    """P2 playground: LO-MCP similarity of every tool to the query and the subset that would be bound."""
    from secondbrain.lomcp.predictor import get_index, predict_tools

    info = _quota_safe(lambda: predict_tools(body.query))
    index = get_index()
    tools = [
        {"name": t.name, "description": t.description, "tokens": index.entries[t.name]["tokens"],
         "score": info["scores"].get(t.name), "selected": t.name in info["names"]}
        for t in index.tools
    ]
    tools.sort(key=lambda t: t["score"] or 0, reverse=True)
    return {**info, "tools": tools, "thresholds": {
        "top_k": settings.lomcp_top_k, "margin": settings.lomcp_margin, "min_sim": settings.lomcp_min_sim}}


@router.get("/memories")
def get_memories(user_id: str = "default"):
    from secondbrain.agent.service import list_memories

    return _quota_safe(lambda: list_memories(user_id=user_id))


@router.post("/memories")
def add_memory(body: MemoryIn):
    from secondbrain.agent.service import remember

    return _quota_safe(lambda: remember(text=body.text, user_id=body.user_id))


@router.delete("/memories/{memory_id}")
def delete_memory(memory_id: str):
    from secondbrain.agent.service import forget

    return _quota_safe(lambda: forget(memory_id=memory_id))


@router.get("/memories/history")
def memory_history(user_id: str = "default"):
    """AAM audit trail: memories deprecated by a later contradicting fact."""
    from secondbrain.memory.status_store import get_status_store

    try:
        rows = get_status_store().history(user_id)
    except Exception as e:
        logger.warning(f"memory history unavailable: {e}")
        rows = []
    return {"history": sorted(rows, key=lambda r: r.get("deprecated_at") or "", reverse=True)}
