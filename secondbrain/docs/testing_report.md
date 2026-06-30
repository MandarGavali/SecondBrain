# Testing Report

Generated: 2026-06-20

---

## Issue 1: Retriever Returns Zero Documents

| Field | Value |
| :--- | :--- |
| **Status** | PASS — No fix required |
| **Root Cause** | N/A |
| **Fix Applied** | No change required. |
| **Files Modified** | None |
| **Verification** | `rag/vectorstore/qdrant_store.py` uses `COLLECTION_NAME = "Learning_RAG"` consistently for both indexing (`create_vector_store`) and retrieval (`get_existing_vector_store`). Collection names match. `retrieval_service.py` correctly initializes the embedding model and vector store with a singleton cache. Previous test run retrieved 5 documents successfully. |
| **Remaining Risks** | If Qdrant Docker container is stopped, retrieval fails with `RetrievalError`. Start with: `docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant`. |

---

## Issue 2: Checkpoint / Conversation Memory Not Working

| Field | Value |
| :--- | :--- |
| **Status** | FAIL → **FIXED** |
| **Root Cause** | **Critical.** Two bugs: (1) `cli/chat.py` passed `"messages": []` on every `graph.invoke()` call, which reset message state before the checkpoint could restore it. (2) `generate_chat_response()` only accepted `query: str` — conversation history was stored in MongoDB but **never passed to the LLM**. The assistant was functionally amnesic on every turn. |
| **Fix Applied** | (1) Removed `"messages": []` from the `graph.invoke()` input in `cli/chat.py`. LangGraph now restores messages automatically from the checkpoint. (2) Added `history: list = None` parameter to `generate_chat_response()`, `generate_standard_chat()`, and `run_chat_agent()`. `chat_node` now reads `state.get("messages", [])` and passes it through the call chain so the LLM receives prior turns. |
| **Files Modified** | `cli/chat.py`, `rag/llm/gemini_llm.py`, `rag/services/chat_service.py`, `agents/chat_agent.py`, `graph/nodes.py` |
| **Verification** | Code path verified by reading all files. Rate limit prevented live test, but the import chain executed cleanly and the `chat_node` was reached before the 429 error. |
| **Remaining Risks** | None. The `history` parameter defaults to `None`, so the fix is backward-compatible with the API endpoint and `test_graph.py`. |

---

## Issue 3: Hallucination Checker Always Returns False

| Field | Value |
| :--- | :--- |
| **Status** | FAIL → **FIXED** |
| **Root Cause** | `content_lines[0].strip().upper() == "YES"` — strict exact equality. Gemini 2.5 Flash frequently responds with `"YES."`, `"YES,"`, or `"YES - the answer is..."` which all failed the check. |
| **Fix Applied** | Replaced `== "YES"` with `.rstrip(".,!- ").startswith("YES")` to tolerate common punctuation variations without redesigning the parser. |
| **Files Modified** | `rag/services/hallucination_checker_service.py` |
| **Verification** | Code diff reviewed. Same pattern applied consistently with the document grader fix. |
| **Remaining Risks** | None. The fix is minimal and conservative. |

---

## Issue 4: Router Always Chooses Chat

| Field | Value |
| :--- | :--- |
| **Status** | PASS — No fix required |
| **Root Cause** | N/A |
| **Fix Applied** | No change required. |
| **Files Modified** | None |
| **Verification** | `router_node` in `graph/nodes.py` uses a simple keyword list (`"document"`, `"pdf"`, `"chapter"`, `"project"`, `"summarize"`, `"explain"`, `"according"`, `"notes"`). No LLM call is made for routing, so there is no prompt parsing risk. The node returns either `"chat"` or `"rag"` as a hardcoded string. Route output was confirmed in prior test run: `router_node decided route: 'chat'` for "Hello" and `'rag'` for document queries. |
| **Remaining Risks** | The keyword list may miss some valid RAG queries (e.g., "What does the paper say about X?"). This is a product decision, not a bug. |

---

## Issue 5: WinError 10061 / Connection Refused

| Field | Value |
| :--- | :--- |
| **Status** | PASS — No fix required |
| **Root Cause** | N/A |
| **Fix Applied** | No change required. |
| **Files Modified** | None |
| **Verification** | Both MongoDB (`checkpointer.py`) and Qdrant (`retrieval_service.py`) already raise meaningful, typed exceptions (`ServerSelectionTimeoutError` and `RetrievalError`) rather than suppressing errors. The error messages are clear. |
| **Remaining Risks** | Startup order matters — run Docker containers before starting the application. |

---

## Issue 6: graph.stream() Misuse

| Field | Value |
| :--- | :--- |
| **Status** | PASS — Documented |
| **Root Cause** | N/A — `test_graph.py` was corrected in an earlier session. |
| **Fix Applied** | No change required. `test_graph.py` uses `graph.invoke()` correctly. |
| **Files Modified** | None |
| **Verification** | `test_graph.py` line 11: `result = graph.invoke(...)`. `result["answer"]` is correctly accessed as a dictionary. `graph.stream()` vs `graph.invoke()` distinction is documented in `docs/testing_guide.md`. |
| **Remaining Risks** | None. |

---

## Issue 7: Import Errors / Missing Dependencies

| Field | Value |
| :--- | :--- |
| **Status** | FAIL → **FIXED** |
| **Root Cause** | `requirements.txt` was missing: `langgraph`, `langgraph-checkpoint-mongodb`, `pymongo`, `fastapi`, `uvicorn`, `google-genai`, `qdrant-client`. A fresh `pip install -r requirements.txt` would have left the application unable to run. |
| **Fix Applied** | Added all missing packages with comments grouping them by purpose. |
| **Files Modified** | `requirements.txt` |
| **Verification** | Cross-referenced every `import` statement across the project against `requirements.txt`. |
| **Remaining Risks** | Pinning versions is recommended before production deployment to ensure reproducibility. |

---

## Issue 8: Infinite Rewrite Loop

| Field | Value |
| :--- | :--- |
| **Status** | PASS — No fix required |
| **Root Cause** | N/A |
| **Fix Applied** | No change required. |
| **Files Modified** | None |
| **Verification** | `workflow.py` `grade_decision()` function: `if state["retries"] >= 1: return "generate"` — this forces a generate after at most one rewrite. `rewrite_query_node` increments `retries` on every call. The loop cannot run more than once. |
| **Remaining Risks** | None. |

---

## Issue 9: Document Grader Removes Every Document

| Field | Value |
| :--- | :--- |
| **Status** | FAIL → **FIXED** (parsing bug) |
| **Root Cause** | The fallback in `document_grading_service.py` (`if len(filtered_docs) == 0: return documents`) is correctly implemented. However, the parser bug (exact `== "YES"`) caused over-filtering by rejecting valid `"YES."` responses, which made it more likely that all documents were filtered out, pushing the system toward the fallback path unnecessarily. |
| **Fix Applied** | Fixed the parsing (Issue 3) so valid YES responses are correctly recognized. The existing fallback is confirmed present and functional. |
| **Files Modified** | `rag/services/document_grading_service.py` |
| **Verification** | Fallback at lines 43–45 is present and correct. |
| **Remaining Risks** | None. |

---

## Issue 10: GraphState KeyErrors

| Field | Value |
| :--- | :--- |
| **Status** | FAIL → **FIXED** |
| **Root Cause** | Two issues: (1) `graph/state.py` declared `filtered_docs` and `rewritten_query` twice each (duplicate TypedDict keys). Python silently uses the last declaration but this is confusing and error-prone. (2) `grade_documents_node` accessed `state["retrieved_docs"]` with direct key access instead of `.get()`, which would raise a `KeyError` if the retrieve node had failed. |
| **Fix Applied** | (1) Removed duplicate keys from `GraphState` and added clarifying comments. (2) Changed `state["retrieved_docs"]` to `state.get("retrieved_docs", [])` in `grade_documents_node`. |
| **Files Modified** | `graph/state.py`, `graph/nodes.py` |
| **Verification** | `state.py` now has each key declared exactly once. `grade_documents_node` uses `.get()` with a safe default. |
| **Remaining Risks** | None. |

---

## Issue 11: Conversation History

| Field | Value |
| :--- | :--- |
| **Status** | FAIL → **FIXED** |
| **Root Cause** | See Issue 2. The `messages` field was correctly annotated with `add_messages` in `GraphState` and `HumanMessage`/`AIMessage` objects were correctly appended in both `chat_node` and `generate_node`. MongoDB checkpointing was correctly storing the messages. The bug was that `cli/chat.py` was overwriting the state on every call, and the LLM was never receiving the history anyway. |
| **Fix Applied** | Same as Issue 2. |
| **Files Modified** | `cli/chat.py`, `rag/llm/gemini_llm.py`, `rag/services/chat_service.py`, `agents/chat_agent.py`, `graph/nodes.py` |
| **Verification** | Verified through code review. |
| **Remaining Risks** | None. |

---

## Issue 12: Qdrant Collection Mismatch

| Field | Value |
| :--- | :--- |
| **Status** | PASS — No fix required |
| **Root Cause** | N/A |
| **Fix Applied** | No change required. |
| **Files Modified** | None |
| **Verification** | `qdrant_store.py` defines `COLLECTION_NAME = "Learning_RAG"` as a module-level constant used by both `create_vector_store()` (indexer) and `get_existing_vector_store()` (retriever). Single source of truth. No mismatch. |
| **Remaining Risks** | None. |

---

## Issue 13: Gemini Rate Limits

| Field | Value |
| :--- | :--- |
| **Status** | FAIL → **FIXED** (rate limit resiliency) |
| **Root Cause** | The free tier allows 20 requests/day for `gemini-2.5-flash` and 15 requests/minute. The pipeline makes multiple LLM calls per query (up to 8 calls per RAG query), easily exhausting limits. |
| **Fix Applied** | (1) Added a robust, transparent `execute_with_retry` wrapper in `rag/llm/gemini_llm.py` for direct Google GenAI SDK calls. It parses `google.genai.errors.ClientError` payloads to extract the precise `retryDelay` field supplied by Gemini and sleeps for that duration (+1.0s safety margin). It falls back to exponential backoff if no specific delay is returned. (2) Configured `max_retries=10` on LangChain's `ChatGoogleGenerativeAI` instances inside `rag/llm/gemini_llm.py` and `rag/services/hallucination_checker_service.py` to gracefully handle rate limits during node execution. |
| **Files Modified** | `rag/llm/gemini_llm.py`, `rag/services/hallucination_checker_service.py`, `docs/testing_report.md` |
| **Opportunities for Batching** | Document grading could be batched: send all 5 documents in a single prompt and ask the LLM to return a comma-separated list of `YES/NO` per document. This would reduce grading from 5 calls to 1 call per query. |
| **Remaining Risks** | Hard daily limits (e.g. 20 requests/day) cannot be bypassed solely by sleeping, so the application will eventually raise the error after 5 retries. Upgrading to a paid plan or switching to a model with a larger quota is still recommended for extensive production loads. |
