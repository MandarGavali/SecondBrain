# Implementation Notes — Research Extensions (P1–P4)

Companion to `SecondBrain_Implementation_Spec.md`. Per spec rule 0.4, this file records every
VERIFY result, every deviation from the spec, and the calibrated thresholds.

Commits: `53bf071` (Phase 0), `f3c673d` (Phase 1), `e8a3106` (Phase 2).

---

## 1. Phase 0 pre-checks (VERIFY results)

| Check | Expected | Result |
|---|---|---|
| `python --version` | 3.12.x | **3.12.15** inside the Docker image (`python:3.12-slim`). `runtime.txt` pins `python-3.12.10` for Render. |
| `import secondbrain.rag.retriever.retriever` (D1) | `NameError` → apply fix 0.2 | Imports cleanly. The D1 import fix was already applied in commit `afdc5bc` ("Restore imports in retriever type hints") before the spec work began. Phase 0 still rewrote the file (spec 0.2) to add `retrieve_documents_with_scores`, which backs `retrieval_service.retrieve_with_scores`. |
| `inspect.signature(mem0.Memory.add)` | has an `infer` parameter | **Yes.** The `TypeError` fallback in `LongTermMemory.save_memory` is kept but is not exercised with the pinned Mem0. |
| `inspect.signature(run_chat_agent)` | `(query, history=...)` | **Matches**: `run_chat_agent(query, history=None)`. `chat_node` calls it as specified. |
| `pip show rq` | pin the installed version (D4) | **2.12.0**, pinned in `requirements.txt`. |

---

## 2. Deviations from the spec

### 2.1 `quality_filter.filter_chunks`: TOC check runs before the low-alpha check
The spec checks `alpha_ratio < QUALITY_MIN_ALPHA` before `looks_like_toc`. Dot leaders
(`Chapter 1 ........ 3`) always push the alphabetic ratio below 0.55, so in the spec's
order a TOC chunk was always rejected as `low_alpha` and `toc_like` could never trigger.
The spec's own unit test (`tests/test_quality_filter.py`, expects a `toc_like` reject)
failed with the original order. The order is now `too_short → toc_like → low_alpha → duplicate`.
The set of rejected chunks is unchanged; only the reported reason differs.

### 2.2 `run_turn`: `no_search` route reports `confidence: "N/A"`
With `ENABLE_VERIFY=1`, a `no_search` turn now reports `"N/A"` instead of `"Unverified"`.
`verify` never runs on the chat path, so `confidence_label` stays `None`, and the spec's
`run_turn` code mapped that to `"Unverified"`. Section 3.3 of the spec defines `N/A` as
"no document evidence used" and reserves `Unverified` for "verification disabled / legacy
mode", so `run_turn` (`agent/service.py`) maps `None` to `"N/A"` on the `no_search` route when
verification is enabled. With `ENABLE_VERIFY=0` it is still `"Unverified"`.

### 2.3 `mcp` dependency pinned to 1.30.0
`mcp` was missing from `requirements.txt`, even though `mcp_server/` imports
`mcp.server.fastmcp.FastMCP`. It is pinned to `mcp==1.30.0` because mcp 2.x renamed `FastMCP`
(commit `af131c2`). Spec rule 0.3 ("no new runtime dependencies") is respected in spirit: this
restores a dependency the code already used.

### 2.4 Where the tests run
The local Windows venv is Python 3.13 with no project dependencies installed, so the test
suite was run inside the Docker image (Python 3.12). On any Python 3.12 environment,
`pip install -r requirements-dev.txt && pytest -q` from the repo root works unchanged.
`tests/conftest.py` sets a dummy `GOOGLE_API_KEY` and `MONGODB_URI` so that import-time
clients can be constructed. No network call is made.

---

## 3. Known issues and observations

- **Thresholds are not calibrated yet.** With only one small document indexed, the top-1
  similarity is about 0.65–0.70 for *every* query, answerable or not. An unanswerable question
  was delivered with `confidence: "High"` (score 0.79). The defaults in `secondbrain/config.py`
  (`CONF_SCORE_REL_MIN=0.50`, `CONF_ABSTAIN=0.30`, …) assume a wider score spread than
  `gemini-embedding-2` produces. **The thresholds MUST be calibrated (Phase 4,
  `python -m eval.calibrate eval/data/queries.jsonl`) before production is switched to
  `GRAPH_MODE=adaptive`.**
- **Gemini free-tier rate limits.** Per-minute 429s add up to about 60 s of latency per
  affected call, because of the existing retry sleeps (`execute_with_retry` in
  `generate_answer` and `max_retries=10` on the LangChain client). Latency numbers from
  free-tier runs are therefore not representative. Run the evaluation configs sequentially.
  The free tier also caps `gemini-2.5-flash` at **20 requests/day**, which is far too few for
  a full ablation run.
- **Fixed during verification: daily quota hang.** `execute_with_retry` used to sleep for the
  server's whole `retryDelay`, which is about 14 h for a daily quota. That held the request and a
  uvicorn worker thread hostage. It now fails fast when the delay exceeds 65 s or the quota is
  `PerDay`, and `/chat` maps `RESOURCE_EXHAUSTED` to HTTP 503 (checked live: 503 in about 2 s).
- **Fixed during verification: retrieval failure.** `retrieve_node` now falls back to "no
  evidence" (answer `NO_INFO_MESSAGE`, confidence `N/A`) instead of raising HTTP 500 when
  embeddings or Qdrant are unreachable (spec rule 5).
- **Not yet verified live (quota exhausted on 2026-10-14):** the AAM conflict flow with the real
  Gemini judge (the plumbing passed with a stubbed LLM against real Mem0, Qdrant and Mongo: the
  old fact was deprecated and recall returned only the new one), the abstain path, and the
  background `session_end` reflection. Rerun spec Section 7 items 3, 6 and 7 once the quota resets.
- **`discover_tools` covers the agent's tools, not the MCP tools.** The LO-MCP index is built from
  `agent/tools.py:get_tools()`. `discover_tools` therefore returns agent tool schemas (for example
  `list_documents`, which is not an MCP tool), in LangChain/OpenAI function format.
- **Import-time MemoryManager (pre-existing).** `graph/agent_node.py` (module level) and
  `agent/service.py` (`_memory_manager = MemoryManager()`) instantiate `MemoryManager` at
  import time. Importing `secondbrain.agent.service`, `api/chat.py` or the MCP server
  therefore needs live Qdrant (Mem0) and MongoDB, even though the graphs themselves are now
  built lazily. Both files were left untouched on purpose (spec Section 12).
- **The complex route often reports `confidence: "N/A"`.** Evidence is only captured from the
  `search_documents` tool artifact. When the agent answers with `list_documents`,
  `summarize_documents` or `generate_questions` only, `collect_evidence` finds no evidence,
  `verify` returns `N/A`, and the answer is delivered unverified.
- **Legacy mode plus AAM.** In `GRAPH_MODE=agent`, `graph/agent_node.py` still performs its
  synchronous per-turn Mem0 save. `end_session` / `session_end=true` additionally schedules
  AAM reflection when `ENABLE_AAM=1`. Memory can therefore be written twice in legacy mode.

---

## 4. Final thresholds (Phase 4)

**TODO:** fill this in after running `python -m eval.calibrate eval/data/queries.jsonl` on the
demo documents (30–50 queries, about half of them unanswerable). Copy the same values into `.env`.

| Env var | Default | Calibrated value | Notes |
|---|---|---|---|
| `CONF_SCORE_REL_MIN` | 0.50 | TODO | Midpoint between the unanswerable median and the answerable p10 (printed by `calibrate`). |
| `CONF_ABSTAIN` | 0.30 | TODO | Unanswerable queries should abstain, and at least 90% of answerable ones should be delivered. |
| `CONF_HIGH` | 0.70 | TODO | |
| `CONF_MEDIUM` | 0.45 | TODO | |
| `LOMCP_MIN_SIM` | 0.30 | TODO | Print `predict_tools(q)["scores"]` for about 10 queries. |
| `LOMCP_MARGIN` | 0.08 | TODO | Too loose → every tool is selected. |

Calibration data: TODO (number of queries, documents used, answerable median / p10,
unanswerable median / p90).
