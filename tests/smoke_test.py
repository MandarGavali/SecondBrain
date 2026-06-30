import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

def run_smoke_tests():
    print("====================================================")
    print("SecondBrain Smoke Test")
    print("====================================================")

    total_tests = 8
    passed_tests = 0

    def log_result(name, success, reason=""):
        nonlocal passed_tests
        if success:
            print(f"[PASS] {name}")
            passed_tests += 1
        else:
            print(f"[FAIL] {name} - {reason}")

    # Test 1: Logger initialized
    try:
        from secondbrain.core.logger import get_logger
        logger = get_logger("smoke_test")
        # Ensure we don't spam the console too much by default, but we'll log it
        logger.info("Running smoke tests...")
        log_result("Logger initialized", True)
    except Exception as e:
        log_result("Logger initialized", False, str(e))
        logger = None

    # Test 2: LangGraph compiled
    try:
        from secondbrain.graph.workflow import compile_graph_with_checkpointer
        graph = compile_graph_with_checkpointer()
        if graph:
            log_result("LangGraph compiled", True)
        else:
            log_result("LangGraph compiled", False, "Graph object is None")
    except Exception as e:
        if logger: logger.exception("LangGraph failed")
        log_result("LangGraph compiled", False, str(e))

    # Test 3: Gemini initialized
    try:
        from secondbrain.rag.llm.gemini_llm import get_llm
        llm = get_llm()
        if llm:
            log_result("Gemini initialized", True)
        else:
            log_result("Gemini initialized", False, "LLM object is None")
    except Exception as e:
        if logger: logger.exception("Gemini failed")
        log_result("Gemini initialized", False, str(e))

    # Test 4: Qdrant connection
    try:
        from secondbrain.rag.embeddings.gemini_embeddings import get_embedding_model
        from secondbrain.rag.vectorstore.qdrant_store import get_existing_vector_store
        embedding_model = get_embedding_model()
        vector_store = get_existing_vector_store(embedding_model)
        if vector_store:
            log_result("Qdrant connection", True)
        else:
            log_result("Qdrant connection", False, "Vector store object is None")
    except Exception as e:
        if logger: logger.exception("Qdrant failed")
        log_result("Qdrant connection", False, str(e))

    # Test 5: Retriever returned documents
    try:
        from secondbrain.rag.services.retrieval_service import retrieve_relevant_documents
        # PASS if at least one document is returned
        docs = retrieve_relevant_documents("What is RAG?", k=1)
        if isinstance(docs, list):
            if len(docs) > 0:
                log_result("Retriever returned documents", True)
            else:
                log_result("Retriever returned documents", False, "No documents returned (index might be empty)")
        else:
            log_result("Retriever returned documents", False, "Invalid return type")
    except Exception as e:
        if logger: logger.exception("Retriever failed")
        log_result("Retriever returned documents", False, str(e))

    # Test 6: Memory manager operational
    try:
        from secondbrain.memory.memory_manager import MemoryManager
        manager = MemoryManager()
        test_user = f"smoke_test_user_{uuid.uuid4()}"
        manager.save_long_term(test_user, [{"role": "user", "content": "I like python."}])
        results = manager.get_long_term(test_user, "What do I like?")
        if results and isinstance(results, dict):
            log_result("Memory manager operational", True)
        else:
            log_result("Memory manager operational", False, "Invalid memory retrieval format")
    except Exception as e:
        if logger: logger.exception("Memory failed")
        log_result("Memory manager operational", False, str(e))

    # Test 7: MCP tools registered
    try:
        from secondbrain.mcp_server.server import mcp
        if mcp and mcp.name == "SecondBrain":
            log_result("MCP tools registered", True)
        else:
            log_result("MCP tools registered", False, "FastMCP instance not found or invalid")
    except Exception as e:
        if logger: logger.exception("MCP failed")
        log_result("MCP tools registered", False, str(e))

    # Test 8: Chat pipeline executed
    try:
        from secondbrain.agent.service import answer_query
        test_thread = f"smoke_test_thread_{uuid.uuid4()}"
        response = answer_query("Hello", thread_id=test_thread)
        if response:
            log_result("Chat pipeline executed", True)
        else:
            log_result("Chat pipeline executed", False, "No response from pipeline")
    except Exception as e:
        if logger: logger.exception("Chat pipeline failed")
        log_result("Chat pipeline executed", False, str(e))

    print("====================================================")
    print("Smoke Test Result")
    print(f"{passed_tests} / {total_tests} Tests Passed")
    print("====================================================")

    if passed_tests == total_tests:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_tests()
