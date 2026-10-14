import time
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from secondbrain.agent.agent import create_agent
from secondbrain.agent.tools import get_tools
from secondbrain.config import settings
from secondbrain.core.logger import get_logger
from secondbrain.graph.checkpointer import get_checkpointer
from secondbrain.graph.state import AdaptiveState
from secondbrain.graph.tool_node import tool_node
from secondbrain.lomcp.predictor import predict_tools
from secondbrain.memory.memory_manager import get_memory_manager
from secondbrain.memory.reflection import filter_active
from secondbrain.rag.evidence import doc_to_evidence, evidence_to_doc
from secondbrain.rag.services.generation_service import generate_grounded_answer
from secondbrain.rag.services.hallucination_checker_service import check_hallucination
from secondbrain.rag.services.query_rewriter_service import rewrite_query
from secondbrain.rag.services.retrieval_service import retrieve_with_scores
from secondbrain.routing.classifier import COMPLEX, NO_SEARCH, SIMPLE, VALID_LABELS, classify_query
from secondbrain.utils.text import message_text
from secondbrain.verification.confidence import (
    compute_confidence, decide, label_for, strip_verbal_confidence,
)

logger = get_logger("graph.adaptive")

ABSTAIN_MESSAGE = (
    "I couldn't find enough reliable information in your documents to answer that confidently. "
    "Try rephrasing the question or uploading the relevant document. "
    "I've flagged this question for review."
)
NO_INFO_MESSAGE = "I couldn't find relevant information in your documents for this question."
FALLBACK_MESSAGE = "I wasn't able to produce an answer. Please try rephrasing your question."


def _metric(state, key: str, t0: float, **extra) -> dict:
    m = dict(state.get("metrics") or {})
    m[key] = round((time.perf_counter() - t0) * 1000, 1)
    m.update(extra)
    return m


def new_turn_input(query: str, user_id: str) -> dict:
    """Initial state for one turn. Resets every per-turn field (state is checkpointed per thread)."""
    return {
        "messages": [("user", query)],
        "user_id": user_id,
        "user_query": query,
        "rewritten_query": None,
        "route": None,
        "route_method": None,
        "memory_context": "",
        "selected_tools": [],
        "agent_steps": 0,
        "evidence": [],
        "answer": None,
        "retries": 0,
        "is_grounded": None,
        "verification_reason": None,
        "confidence_score": None,
        "confidence_label": None,
        "abstained": False,
        "needs_review": False,
        "metrics": {},
    }


# ------------------------------------------------------------------ nodes
def recall_memory_node(state: AdaptiveState) -> dict:
    t0 = time.perf_counter()
    uid = state.get("user_id") or "default"
    context = ""
    try:
        mm = get_memory_manager()
        found = mm.get_long_term(user_id=uid, query=state["user_query"])
        active = filter_active(found, uid)
        if active["results"]:
            context = mm.format_memories(active)
    except Exception as e:  # memory must never break answering
        logger.warning(f"recall_memory failed, continuing without memory: {e}")
    return {"memory_context": context, "metrics": _metric(state, "t_memory_ms", t0)}


def classify_node(state: AdaptiveState) -> dict:
    t0 = time.perf_counter()
    forced = (settings.force_route or "").strip().lower()
    if forced in VALID_LABELS:
        label, method = forced, "forced"
    elif not settings.enable_router:
        label, method = COMPLEX, "disabled"
    else:
        result = classify_query(state["user_query"])
        label, method = result["label"], result["method"]
    logger.info(f"route={label} method={method}")
    return {"route": label, "route_method": method, "metrics": _metric(state, "t_classify_ms", t0)}


def route_after_classify(state: AdaptiveState) -> str:
    label = state.get("route")
    return label if label in VALID_LABELS else COMPLEX


def chat_node(state: AdaptiveState) -> dict:
    from secondbrain.agents.chat_agent import run_chat_agent

    t0 = time.perf_counter()
    query = state["user_query"]
    ctx = state.get("memory_context") or ""
    prompt = f"{ctx}\n\nUser question: {query}" if ctx else query
    history = (state.get("messages") or [])[:-1]  # everything before the current user message
    answer = run_chat_agent(query=prompt, history=history)
    return {"answer": message_text(answer), "metrics": _metric(state, "t_chat_ms", t0)}


def select_tools_node(state: AdaptiveState) -> dict:
    """LO-MCP: decide which tool schemas the LLM will see."""
    t0 = time.perf_counter()
    all_names = [t.name for t in get_tools()]
    extra: dict = {}
    names = all_names
    if settings.enable_lomcp:
        try:
            info = predict_tools(state["user_query"])
            names = info["names"] or all_names
            extra = {"schema_tokens_full": info["tokens_full"],
                     "schema_tokens_selected": info["tokens_selected"]}
        except Exception as e:
            logger.warning(f"LO-MCP prediction failed, exposing all tools: {e}")
    return {
        "selected_tools": names,
        "agent_steps": 0,
        "metrics": _metric(state, "t_select_tools_ms", t0, tools_selected=names, **extra),
    }


@lru_cache(maxsize=32)
def _agent_for(names: tuple):
    by_name = {t.name: t for t in get_tools()}
    return create_agent(tools=[by_name[n] for n in names if n in by_name])


def agent_node(state: AdaptiveState) -> dict:
    t0 = time.perf_counter()
    names = tuple(state.get("selected_tools") or [t.name for t in get_tools()])
    response = _agent_for(names).invoke(
        {"messages": state["messages"], "memory_context": state.get("memory_context") or ""}
    )
    steps = (state.get("agent_steps") or 0) + 1
    return {"messages": [response], "agent_steps": steps,
            "metrics": _metric(state, f"t_agent_{steps}_ms", t0)}


def agent_decision(state: AdaptiveState) -> str:
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None) and (state.get("agent_steps") or 0) < settings.max_agent_steps:
        return "tools"
    return "done"


def collect_evidence_node(state: AdaptiveState) -> dict:
    msgs = state.get("messages") or []
    start = max((i for i, m in enumerate(msgs) if isinstance(m, HumanMessage)), default=0)
    evidence, seen = [], set()
    for m in msgs[start:]:
        artifact = getattr(m, "artifact", None) if isinstance(m, ToolMessage) else None
        if isinstance(artifact, list):
            for e in artifact:
                if isinstance(e, dict) and "text" in e:
                    key = (e.get("document"), e.get("page"), e.get("chunk_id"), e["text"][:80])
                    if key not in seen:
                        seen.add(key)
                        evidence.append(e)
    last = msgs[-1] if msgs else None
    answer = ""
    if isinstance(last, AIMessage) and not getattr(last, "tool_calls", None):
        answer = strip_verbal_confidence(message_text(last.content).strip())
    return {"evidence": evidence, "answer": answer}


def retrieve_node(state: AdaptiveState) -> dict:
    t0 = time.perf_counter()
    retrying = (state.get("retries") or 0) > 0
    query = state.get("rewritten_query") or state["user_query"]
    k = settings.retry_k if retrying else settings.simple_k
    try:
        pairs = retrieve_with_scores(query=query, k=k)
    except Exception as e:  # no evidence -> generate answers "not found" and verify reports N/A
        logger.warning(f"retrieval failed, continuing without evidence: {e}")
        pairs = []
    evidence = [doc_to_evidence(doc, score) for doc, score in pairs]
    return {"evidence": evidence, "metrics": _metric(state, "t_retrieve_ms", t0)}


def generate_node(state: AdaptiveState) -> dict:
    t0 = time.perf_counter()
    evidence = state.get("evidence") or []
    if not evidence:
        return {"answer": NO_INFO_MESSAGE, "metrics": _metric(state, "t_generate_ms", t0)}
    docs = [evidence_to_doc(e) for e in evidence]
    answer = generate_grounded_answer(query=state["user_query"], documents=docs)
    return {"answer": strip_verbal_confidence(answer), "metrics": _metric(state, "t_generate_ms", t0)}


def verify_node(state: AdaptiveState) -> dict:
    """P4 stage 2: measured confidence + groundedness."""
    t0 = time.perf_counter()
    evidence = state.get("evidence") or []
    answer = state.get("answer") or ""

    def out(**kw):
        return {"metrics": _metric(state, "t_verify_ms", t0), **kw}

    if not settings.enable_verify:
        return out(confidence_label=None, confidence_score=None, is_grounded=None)
    if not evidence or not answer:
        return out(confidence_label="N/A", confidence_score=None, is_grounded=None)

    scores = [e["score"] for e in evidence if e.get("score") is not None]
    grounded, reason = None, None
    if state.get("route") != SIMPLE or settings.verify_simple_llm:
        try:
            grounded, reason = check_hallucination(
                answer=answer, documents=[evidence_to_doc(e) for e in evidence]
            )
        except Exception as e:
            logger.warning(f"groundedness check failed, continuing without it: {e}")
    score = compute_confidence(scores, grounded)
    return out(is_grounded=grounded, verification_reason=reason,
               confidence_score=score, confidence_label=label_for(score))


def verify_decision(state: AdaptiveState) -> str:
    if not settings.enable_verify or state.get("confidence_score") is None:
        return "deliver"
    return decide(state.get("is_grounded"), state["confidence_score"], state.get("retries") or 0)


def rewrite_node(state: AdaptiveState) -> dict:
    current = state.get("rewritten_query") or state["user_query"]
    return {"rewritten_query": rewrite_query(current), "retries": (state.get("retries") or 0) + 1}


def abstain_node(state: AdaptiveState) -> dict:
    logger.info(f"Abstaining: grounded={state.get('is_grounded')} score={state.get('confidence_score')}")
    return {"answer": ABSTAIN_MESSAGE, "abstained": True, "needs_review": True}


def finalize_node(state: AdaptiveState) -> dict:
    t0 = time.perf_counter()
    answer = (state.get("answer") or "").strip() or FALLBACK_MESSAGE
    msgs = state.get("messages") or []
    last = msgs[-1] if msgs else None
    new_msgs: list = []

    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        # step limit hit with a dangling tool call: close it so the history stays valid for Gemini
        for tc in last.tool_calls:
            new_msgs.append(ToolMessage(content="Skipped: step limit reached.", tool_call_id=tc["id"]))
        new_msgs.append(AIMessage(content=answer))
    elif isinstance(last, AIMessage) and last.id:
        if message_text(last.content).strip() != answer:
            new_msgs.append(AIMessage(content=answer, id=last.id))  # same id -> replaces the message
    else:
        new_msgs.append(AIMessage(content=answer))

    if not settings.enable_aam and not state.get("abstained"):
        try:  # baseline behaviour: synchronous per-turn memory write
            get_memory_manager().extract_and_save_memory(
                user_id=state.get("user_id") or "default",
                user_message=state["user_query"],
                assistant_message=answer,
            )
        except Exception as e:
            logger.warning(f"per-turn memory save failed: {e}")

    return {"answer": answer, "messages": new_msgs, "metrics": _metric(state, "t_finalize_ms", t0)}


# ------------------------------------------------------------------ graph
def create_adaptive_graph(checkpointer=None):
    b = StateGraph(AdaptiveState)
    b.add_node("recall_memory", recall_memory_node)
    b.add_node("classify", classify_node)
    b.add_node("chat", chat_node)
    b.add_node("select_tools", select_tools_node)
    b.add_node("agent", agent_node)
    b.add_node("tools", tool_node)
    b.add_node("collect_evidence", collect_evidence_node)
    b.add_node("retrieve", retrieve_node)
    b.add_node("generate", generate_node)
    b.add_node("verify", verify_node)
    b.add_node("rewrite", rewrite_node)
    b.add_node("abstain", abstain_node)
    b.add_node("finalize", finalize_node)

    b.add_edge(START, "recall_memory")
    b.add_edge("recall_memory", "classify")
    b.add_conditional_edges(
        "classify", route_after_classify,
        {NO_SEARCH: "chat", SIMPLE: "retrieve", COMPLEX: "select_tools"},
    )
    b.add_edge("chat", "finalize")
    b.add_edge("select_tools", "agent")
    b.add_conditional_edges("agent", agent_decision, {"tools": "tools", "done": "collect_evidence"})
    b.add_edge("tools", "agent")
    b.add_edge("collect_evidence", "verify")
    b.add_edge("retrieve", "generate")
    b.add_edge("generate", "verify")
    b.add_conditional_edges(
        "verify", verify_decision, {"deliver": "finalize", "retry": "rewrite", "abstain": "abstain"}
    )
    b.add_edge("rewrite", "retrieve")
    b.add_edge("abstain", "finalize")
    b.add_edge("finalize", END)

    return b.compile(checkpointer=checkpointer if checkpointer is not None else get_checkpointer())
