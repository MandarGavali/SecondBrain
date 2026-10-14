from secondbrain.routing.classifier import classify_query, heuristic_classify


def test_heuristics():
    assert heuristic_classify("hi")[0] == "no_search"
    assert heuristic_classify("Compare the leave policy of 2024 and 2025")[0] == "complex"
    assert heuristic_classify("What are the library timings?")[0] == "simple"
    assert heuristic_classify("tell me about leave rules")[0] is None


def test_hybrid_uses_llm_when_unsure(monkeypatch):
    monkeypatch.setenv("ROUTER_MODE", "hybrid")
    r = classify_query("tell me about leave rules", llm_call=lambda p: "simple")
    assert r["label"] == "simple" and r["method"] == "llm"


def test_llm_failure_falls_back_to_complex(monkeypatch):
    monkeypatch.setenv("ROUTER_MODE", "hybrid")

    def boom(_):
        raise RuntimeError("quota")

    r = classify_query("tell me about leave rules", llm_call=boom)
    assert r["label"] == "complex"


def test_heuristic_mode_unsure_is_complex(monkeypatch):
    monkeypatch.setenv("ROUTER_MODE", "heuristic")
    assert classify_query("tell me about leave rules")["label"] == "complex"
