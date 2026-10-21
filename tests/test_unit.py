"""
Offline unit tests: no Gemini, Qdrant, MongoDB or Redis required.

Run with:  python -m pytest -q
(The end-to-end checks against real services live in tests/smoke_test.py.)
"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from secondbrain.api import upload as upload_module
from secondbrain.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("notes.pdf", "notes.pdf"),
        ("../../etc/evil.pdf", "evil.pdf"),
        ("..\\..\\windows\\evil.pdf", "evil.pdf"),
        ("/abs/path/doc.PDF", "doc.PDF"),
        (None, ""),
    ],
)
def test_safe_filename_strips_directories(raw, expected):
    assert upload_module._safe_filename(raw) == expected


def test_upload_rejects_non_pdf():
    response = client.post("/upload", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 400


def test_upload_sync_mode_returns_chunk_count(monkeypatch, tmp_path):
    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        upload_module,
        "process_pdf",
        lambda path: {"chunks_indexed": 7, "status": "success", "message": "ok"},
    )

    response = client.post(
        "/upload", files={"file": ("../../Report.PDF", b"%PDF-1.4", "application/pdf")}
    )

    assert response.status_code == 200
    assert response.json()["chunks_indexed"] == 7
    saved = list(tmp_path.iterdir())
    assert len(saved) == 1 and saved[0].name.endswith("_Report.PDF")


def test_upload_corrupt_pdf_is_client_error_and_cleaned_up(monkeypatch, tmp_path):
    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    response = client.post(
        "/upload", files={"file": ("broken.pdf", b"not really a pdf", "application/pdf")}
    )

    assert response.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_upload_queue_mode_enqueues(monkeypatch, tmp_path):
    import secondbrain.queues.client as queue_client

    monkeypatch.setenv("UPLOAD_MODE", "queue")
    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    enqueued = []

    class FakeQueue:
        def enqueue(self, func, path):
            enqueued.append(path)
            return SimpleNamespace(id="job-123", get_status=lambda: "queued")

    monkeypatch.setattr(queue_client, "queue", FakeQueue())

    response = client.post(
        "/upload", files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")}
    )

    assert response.status_code == 200
    assert response.json()["job_id"] == "job-123"
    assert len(enqueued) == 1


def test_chat_accepts_int_and_str_thread_ids(monkeypatch):
    import secondbrain.api.chat as chat_module

    calls = []

    def fake_answer_query(query, thread_id, user_id):
        calls.append((query, thread_id, user_id))
        return "answer"

    monkeypatch.setattr(chat_module, "answer_query", fake_answer_query)

    assert client.post("/chat", json={"query": "hi", "thread_id": 42}).status_code == 200
    assert client.post("/chat", json={"query": "hi", "thread_id": "abc"}).status_code == 200
    assert client.post("/chat", json={"query": "hi"}).status_code == 200
    assert [c[1] for c in calls] == ["42", "abc", "default"]


# ---------------------------------------------------------------------------
# Agent node / memory
# ---------------------------------------------------------------------------

class FakeMemoryManager:
    def __init__(self, fail=False):
        self.fail = fail
        self.searched = []
        self.saved = []

    def get_long_term(self, user_id, query):
        if self.fail:
            raise RuntimeError("qdrant down")
        self.searched.append(query)
        return {"results": [{"memory": "User codes in Python"}]}

    def format_memories(self, memories):
        from secondbrain.memory.memory_manager import MemoryManager

        return MemoryManager.format_memories(None, memories)

    def extract_and_save_memory(self, user_id, user_message, assistant_message):
        if self.fail:
            raise RuntimeError("qdrant down")
        self.saved.append((user_message, assistant_message))


class FakeAgent:
    def __init__(self, response):
        self.response = response
        self.inputs = []

    def invoke(self, inputs):
        self.inputs.append(inputs)
        return self.response


def _run_agent_node(monkeypatch, messages, response, memory):
    import secondbrain.graph.agent_node as node

    agent = FakeAgent(response)
    monkeypatch.setattr(node, "get_agent", lambda: agent)
    monkeypatch.setattr(node, "get_memory_manager", lambda: memory)
    result = node.agent_node({"messages": messages, "user_id": "u1"})
    return result, agent


def test_agent_node_uses_last_human_message_after_tool_call(monkeypatch):
    memory = FakeMemoryManager()
    messages = [
        HumanMessage(content="What does chapter 2 say?"),
        AIMessage(content="", tool_calls=[{"name": "search_documents", "args": {"query": "chapter 2"}, "id": "1"}]),
        ToolMessage(content="[1] Source: book.pdf ... raw chunk text", tool_call_id="1"),
    ]
    final = AIMessage(content=[{"type": "text", "text": "Chapter 2 covers RAG."}])

    _, agent = _run_agent_node(monkeypatch, messages, final, memory)

    assert memory.searched == ["What does chapter 2 say?"]
    assert memory.saved == [("What does chapter 2 say?", "Chapter 2 covers RAG.")]
    assert "User codes in Python" in agent.inputs[0]["memory_context"]


def test_agent_node_does_not_save_memory_for_tool_call_turns(monkeypatch):
    memory = FakeMemoryManager()
    tool_call = AIMessage(content="", tool_calls=[{"name": "list_documents", "args": {}, "id": "1"}])

    _run_agent_node(monkeypatch, [HumanMessage(content="list my docs")], tool_call, memory)

    assert memory.saved == []


def test_agent_node_survives_memory_outage(monkeypatch):
    memory = FakeMemoryManager(fail=True)
    final = AIMessage(content="Hello!")

    result, agent = _run_agent_node(monkeypatch, [HumanMessage(content="hi")], final, memory)

    assert result["messages"] == [final]
    assert agent.inputs[0]["memory_context"] == ""


@pytest.mark.parametrize(
    "memories, expected",
    [
        ({"results": [{"memory": "Likes Python"}]}, "Known information about the user:\n- Likes Python"),
        ([{"memory": "Likes Python"}], "Known information about the user:\n- Likes Python"),
        ({"results": []}, ""),
        (None, ""),
    ],
)
def test_format_memories_handles_mem0_shapes(memories, expected):
    from secondbrain.memory.memory_manager import MemoryManager

    assert MemoryManager.format_memories(None, memories) == expected


def test_long_term_get_memory_context_reads_memory_field():
    from secondbrain.memory.long_term import LongTermMemory

    ltm = LongTermMemory.__new__(LongTermMemory)  # skip Mem0/Qdrant setup
    ltm.memory = SimpleNamespace(
        search=lambda query, filters, limit: {"results": [{"memory": "A"}, {"memory": "B"}]}
    )

    assert ltm.get_memory_context(user_id="u", query="q") == "A\nB"


# ---------------------------------------------------------------------------
# Retrieval / tools / exceptions
# ---------------------------------------------------------------------------

def test_retrieve_documents_returns_docs_without_scores():
    from secondbrain.rag.retriever.retriever import retrieve_documents

    docs = [Document(page_content="a"), Document(page_content="b")]
    store = SimpleNamespace(similarity_search_with_score=lambda q, k: [(d, 0.9) for d in docs])

    assert retrieve_documents("q", store, k=2) == docs


def test_agent_search_tool_returns_readable_text(monkeypatch):
    import secondbrain.agent.tools as agent_tools

    monkeypatch.setattr(
        agent_tools,
        "search_documents",
        lambda query, k: [
            Document(page_content="RAG combines retrieval and generation.",
                     metadata={"document_name": "notes.pdf", "page_label": "3"})
        ],
    )

    text = agent_tools.search_tool.invoke({"query": "what is rag"})

    assert isinstance(text, str)
    assert "notes.pdf" in text and "page 3" in text
    assert "RAG combines retrieval" in text


def test_agent_search_tool_handles_no_results(monkeypatch):
    import secondbrain.agent.tools as agent_tools

    monkeypatch.setattr(agent_tools, "search_documents", lambda query, k: [])

    assert "No relevant documents" in agent_tools.search_tool.invoke({"query": "x"})


def test_exception_hierarchies_are_unified():
    from secondbrain.core.exceptions import RetrieverError, SecondBrainError
    from secondbrain.utils.exceptions import GenerationError, RetrievalError

    assert RetrievalError is RetrieverError
    assert issubclass(GenerationError, SecondBrainError)


def test_ingest_rejects_pdf_without_text(monkeypatch):
    import secondbrain.rag.pipeline as pipeline

    monkeypatch.setattr(pipeline, "load_pdf", lambda path: [])

    with pytest.raises(ValueError, match="No extractable text"):
        pipeline.ingest_document("empty.pdf")
