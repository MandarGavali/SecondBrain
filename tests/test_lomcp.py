from langchain_core.tools import StructuredTool

from secondbrain.lomcp import cache
from secondbrain.lomcp.predictor import ToolIndex, cosine, select_names


def test_cosine():
    assert cosine([1, 0], [1, 0]) == 1.0
    assert cosine([1, 0], [0, 1]) == 0.0


def test_select_names_keeps_core_and_never_empty():
    scores = {"search_documents": 0.2, "list_documents": 0.9, "summarize_documents": 0.1}
    assert set(select_names(scores, 3, 0.05, 0.3, ["search_documents"])) == {"list_documents", "search_documents"}
    assert select_names({"a": 0.1, "b": 0.05}, 2, 0.05, 0.5, []) == ["a", "b"]  # fail-safe: all tools


class FakeEmbedder:
    VOCAB = ["document", "list", "summary", "question"]

    def _vec(self, text):
        t = text.lower()
        return [float(t.count(w)) for w in self.VOCAB]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


def _tool(name, desc):
    return StructuredTool.from_function(func=lambda query="": "x", name=name, description=desc)


def test_predict_selects_subset(monkeypatch):
    monkeypatch.setattr(cache, "_get_redis", lambda: None)
    cache._local.clear()
    tools = [
        _tool("search_documents", "search document passages"),
        _tool("list_documents", "list document names"),
        _tool("generate_questions", "generate question practice"),
    ]
    info = ToolIndex(tools, embedder=FakeEmbedder()).predict("please list my document names")
    assert "list_documents" in info["names"] and "search_documents" in info["names"]
    assert "generate_questions" not in info["names"]
    assert info["tokens_selected"] < info["tokens_full"]
