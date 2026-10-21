# Changelog: Repository Cleanup & Bug Fixes (October 2026)

This log covers a cleanup pass made before the project was presented. API
request and response shapes are backward-compatible: `/chat` still accepts
integer `thread_id`s, and `/upload` keeps its existing fields and adds
`chunks_indexed`.

**Before:** the FastAPI app and the MCP server both **crashed on import**, and
the project had no automated tests that could run without live services.
**After:** every module imports cleanly, and `python -m pytest -q` runs **24
offline unit tests**, all of which pass.

## Critical fixes (the app could not start)

| # | Problem | Fix |
|---|---|---|
| 1 | **`NameError: QdrantVectorStore` on startup.** The last commit ("Add retrieval debug logging") commented out the imports in `rag/retriever/retriever.py` but kept the function that uses them in type hints. Importing `secondbrain.main` failed, so `uvicorn`, the CLI and the MCP server all crashed. | Restored the imports. The per-chunk debug lines, which include document text, now log at `DEBUG` instead of `INFO` so document contents stay out of production logs. |
| 2 | **The MCP server could not run.** `mcp` was missing from `requirements.txt`, and the current `mcp` 2.x release removed `mcp.server.fastmcp`, which this code uses. | Pinned `mcp==1.30.0`. |
| 3 | **The app needed MongoDB and Qdrant just to import.** `api/chat.py` compiled the graph at import time, and `graph/agent_node.py` and `agent/service.py` built `MemoryManager()`, which connects to Qdrant, at import time. | The graph and memory manager are now created lazily (thread-safe) on first use. One shared graph (`agent.service.get_graph`) serves the REST API, CLI and MCP server. Previously there were two separately compiled graphs. |

## Bug fixes

| # | Area | Problem | Fix |
|---|---|---|---|
| 4 | `graph/agent_node.py` | After a tool call, `messages[-1]` is a **ToolMessage**. Long-term memory was therefore searched with raw tool output, and Mem0 was asked to save "user said: \<retrieved chunks\>". Memory was also saved on intermediate tool-call turns, where the content is empty. | The node now uses the latest `HumanMessage`, and saves memory only when the agent returns a final answer (no `tool_calls`). |
| 5 | `graph/agent_node.py` | A Mem0 or Qdrant outage made **every chat request fail** with `MemoryError`. | Memory lookup and save are best-effort: a warning is logged and the agent still answers. |
| 6 | `api/upload.py` (security) | **Path traversal.** The client's filename was joined directly into the save path, so `../../x.pdf` could write outside `data/raw/`. A missing filename crashed with `AttributeError`, and `.PDF` was rejected. | Only the base name is kept (Windows separators included). The extension check is case-insensitive. |
| 7 | `api/upload.py` | The `async` endpoint ran blocking PDF loading, embedding and indexing, which **froze the event loop** for all users during an upload. | Now a plain `def` endpoint, which FastAPI runs in its threadpool. |
| 8 | `api/upload.py` | A corrupt or image-only PDF returned **500**, and the file stayed on disk. | Returns **400** with a clear message, and the saved file is deleted on failure. `ingest_document` raises a clear error when a PDF has no extractable text, instead of passing an empty batch to Qdrant. |
| 9 | Upload modes | Redis/RQ queueing was commented out to fit the Render free tier, but the README and `docker-compose.yml` still described the worker flow. | Added `UPLOAD_MODE=sync` (default, for Render) and `UPLOAD_MODE=queue` (set in `docker-compose.yml`, returns a `job_id`). Both flows now work. |
| 10 | `queues/jobs.py`, `agent/service.py` | `ingest_document` returns a dict, but callers treated it as an int. Logs read "indexed {'chunks_indexed': ...} chunks", and the MCP `upload_document` tool returned the whole dict as `chunks_indexed`. | Callers read `result["chunks_indexed"]`. `/upload` now also returns `chunks_indexed`. |
| 11 | `api/jobs.py` | Any error, **including Redis being down**, was reported as "404 Job not found". | 404 only for `NoSuchJobError`, 503 when the queue is unreachable. Finished jobs return their result. |
| 12 | `memory/long_term.py` | `get_memory_context()` read `memory["content"]` from what is actually a dict (`{"results": [{"memory": ...}]}`), so it always crashed. | Reads `results[*]["memory"]`. |
| 13 | `memory/memory_manager.py` | `format_memories()` crashed if Mem0 returned a list instead of a dict. | Handles both shapes. |
| 14 | `core/exceptions.py` | The custom `MemoryError` **shadowed Python's built-in `MemoryError`**. | Renamed to `MemoryStoreError`. |
| 15 | Exceptions | There were two unrelated exception hierarchies. `utils.exceptions.*` errors skipped the API's `SecondBrainError` handler. `tools/search.py`'s `except RetrievalError` never matched the `RetrieverError` that the retrieval service raises. | `utils/exceptions.py` now aliases the classes in `core.exceptions` (`RetrievalError is RetrieverError`), so both names work. |
| 16 | `agent/tools.py` | The agent's `search_documents` tool returned `Document` objects, which ToolNode stringified as Python reprs. | The agent gets readable text with a source document and page for each chunk. |
| 17 | `models/requests.py`, `api/chat.py` | `thread_id` was a **required int**, so the README's chat example (no `thread_id`) returned 422. `/chat` also skipped the Gemini quota handling that the CLI and MCP paths had. | `thread_id: int \| str = "default"`, so existing int clients still work, and `query` must be non-empty. `/chat` goes through `agent.service.answer_query`. |
| 18 | `agent/service.py` | MCP and CLI calls never passed a `user_id`, so all their long-term memories went to one shared "default_user". | `answer_query(..., user_id=None)` defaults `user_id` to `thread_id`. |
| 19 | `rag/pipeline.py` | `answer_query()` returned **hard-coded** `"pages": [1, 4, 9, 13]`. | Returns the page labels of the chunks that were actually retrieved. |
| 20 | `graph/export_graph.py`, `tests/smoke_test.py` | Both imported `compile_graph_with_checkpointer`, which no longer exists, so graph export failed and the smoke test's "LangGraph compiled" check always failed. | Use `create_graph()`. |
| 21 | Model name | `"gemini-2.5-flash"` was hard-coded in five places. | Single `get_model_name()` that reads `GEMINI_MODEL`. The agent, tools, Mem0 and the MCP `system` resource all use it. |
| 22 | Legacy services | `document_grading_service`, `query_rewriter_service` and `hallucination_checker_service` created a Gemini client **at import time**, so importing them without an API key raised an error. | Clients are created on first call. |
| 23 | `.env.example` | `REDIS_URL=redis://localhost:` had no port. | `redis://localhost:6379`. Also documented `GEMINI_MODEL` and `UPLOAD_MODE`. |
| 24 | `cli/chat.py` | It prompted for input at import time and sent empty queries to the agent. | Wrapped in `main()` behind `if __name__ == "__main__"`, and blank input is skipped. |

## Cleanup

- **`requirements.txt`**: added `mcp==1.30.0` and `langchain-text-splitters==1.1.3` (imported directly by the chunker). Pinned `rq==2.12.0`, removed the unused `SQLAlchemy`, and added `pytest`.
- **`docker-compose.yml`**: removed an 80-line commented-out copy of the whole file and set `UPLOAD_MODE: queue` for the API container.
- **Removed dead files**:
  - Three **empty** modules: `rag/loaders/text_loader.py`, `rag/processors/cleaner.py` and `rag/vectorstore/qdrant_client.py`.
  - A stray `rag/loaders/docker-compose.yml` that duplicated the Qdrant service.
  - `rag/loaders/retriever.py`, a scratch script that called `input()` and Gemini **at import time** and duplicated `rag/retriever` and `rag/llm`.
- **Legacy corrective-RAG pipeline kept but labelled**: `graph/nodes.py`, `agents/` and `rag/services/{grading,rewriter,hallucination,generation,chat}`. They are not part of the running graph. `graph/nodes.py`, `agents/README.md` and the commented-out wiring in `graph/workflow.py` are now marked "LEGACY", and the README explains how this pipeline relates to the current agent graph.
- **`main.py`**: imports grouped at the top, and a confusing re-raise inside the global exception handler removed (FastAPI never sends `HTTPException` there).
- **Logging**: per-request `[TIMING]` noise moved to `DEBUG`, and duplicate `logger` imports removed.
- **Unused imports**: removed from 11 files (`ruff --select F401`).
- **`mcp_server/registry.py`**: removed a commented-out duplicate block of registrations.
- **`worker.py`**: removed a commented-out Redis setup that duplicated `queues/client.py`.

## Tests added

- `tests/test_unit.py`: 24 offline tests covering:
  - `/healthz`
  - upload filename sanitisation and path traversal
  - the sync and queue upload modes
  - corrupt-PDF handling and file cleanup
  - `thread_id` compatibility
  - the agent node's memory handling around tool calls and during memory outages
  - Mem0 response parsing
  - retrieval
  - the agent search tool's formatting
  - the unified exception hierarchy
  - rejection of empty PDFs
- `tests/conftest.py`: sets a placeholder API key and adds the project root to `sys.path`.
- `pyproject.toml`: `[tool.pytest.ini_options] testpaths = ["tests"]`.

## Documentation

- **README**:
  - The Request Flow now shows the **actual** agent ↔ tools loop. The old diagram showed the legacy router/grader/rewriter graph.
  - Upload modes, the full env-var table, `/healthz`, a chat example with `thread_id`, MCP memory tool names and a new Testing section were added.
  - The Python version now reads 3.12, matching `runtime.txt` and the Dockerfile, and a duplicated heading was removed.
- `secondbrain/docs/testing_guide.md` and `testing_report.md` are marked as historical because they describe the Phase 4 corrective-RAG graph.

## How to verify

```bash
pip install -r requirements.txt
python -m pytest -q                      # 24 passed, no services needed
uvicorn secondbrain.main:app             # curl localhost:8000/healthz -> {"status":"ok"}
docker compose up --build                # full stack with the RQ worker (UPLOAD_MODE=queue)
python tests/smoke_test.py               # live check against Gemini + MongoDB + Qdrant
```
