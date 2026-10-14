import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

from secondbrain.graph import adaptive


class FakeMM:
    def get_long_term(self, user_id, query, limit=5):
        return {"results": []}

    def format_memories(self, m):
        return ""

    def extract_and_save_memory(self, **kw):
        pass


@pytest.fixture
def graph(monkeypatch):
    monkeypatch.setattr(adaptive, "get_memory_manager", lambda: FakeMM())
    monkeypatch.setattr(adaptive, "filter_active", lambda found, uid: {"results": []})
    monkeypatch.setattr(
        adaptive, "retrieve_with_scores",
        lambda query, k: [(Document(page_content="Leave is 20 days per year.",
                                    metadata={"page_label": "3", "source": "hr.pdf"}), 0.82)],
    )
    monkeypatch.setattr(adaptive, "generate_grounded_answer", lambda query, documents: "20 days.\n\nConfidence:\nHigh")
    monkeypatch.setattr(adaptive, "check_hallucination", lambda answer, documents: (True, "ok"))
    monkeypatch.setattr(adaptive, "rewrite_query", lambda q: q + " (rewritten)")
    for k in ("ENABLE_VERIFY", "FORCE_ROUTE", "ENABLE_LOMCP", "ENABLE_AAM", "ROUTER_MODE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("ROUTER_MODE", "heuristic")
    return adaptive.create_adaptive_graph(checkpointer=MemorySaver())


def run(graph, query, thread="t1"):
    return graph.invoke(adaptive.new_turn_input(query, "u1"), config={"configurable": {"thread_id": thread}})


def test_simple_route_delivers_with_confidence(graph):
    r = run(graph, "What is the annual leave policy?")
    assert r["route"] == "simple"
    assert r["answer"] == "20 days."              # verbal confidence stripped
    assert r["confidence_label"] in {"High", "Medium"}
    assert not r["abstained"]


def test_naive_baseline_flags(graph, monkeypatch):
    monkeypatch.setenv("FORCE_ROUTE", "simple")
    monkeypatch.setenv("ENABLE_VERIFY", "0")
    r = run(graph, "Compare leave policy 2024 and 2025")
    assert r["route"] == "simple" and r["confidence_label"] is None


def test_no_search_route(graph, monkeypatch):
    import secondbrain.agents.chat_agent as chat_agent
    monkeypatch.setattr(chat_agent, "run_chat_agent", lambda query, history=None: "Hello!")
    r = run(graph, "hi")
    assert r["route"] == "no_search" and r["answer"] == "Hello!"


def test_ungrounded_answer_retries_once_then_abstains(graph, monkeypatch):
    monkeypatch.setattr(adaptive, "check_hallucination", lambda answer, documents: (False, "unsupported"))
    monkeypatch.setenv("VERIFY_SIMPLE_LLM", "1")
    r = run(graph, "What is the annual leave policy?")
    assert r["retries"] == 1
    assert r["abstained"] is True and r["needs_review"] is True
    assert r["answer"] == adaptive.ABSTAIN_MESSAGE


def test_complex_route_uses_only_selected_tools(graph, monkeypatch):
    monkeypatch.setenv("ENABLE_LOMCP", "0")
    seen = {}

    class FakeAgent:
        def invoke(self, payload):
            return AIMessage(content="Agent answer", id="ai-1")

    def fake_agent_for(names):
        seen["names"] = names
        return FakeAgent()

    monkeypatch.setattr(adaptive, "_agent_for", fake_agent_for)
    r = run(graph, "Compare the leave policy across all documents")
    assert r["route"] == "complex" and r["answer"] == "Agent answer"
    assert len(seen["names"]) == 4          # LO-MCP disabled -> all tools
    assert r["confidence_label"] == "N/A"   # no document evidence on this path
