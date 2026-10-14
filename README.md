<div align="center">

# 🧠 SecondBrain AI

### Production-Ready AI Personal Knowledge Assistant

*An intelligent knowledge management system powered by Agentic RAG, LangGraph, Long-Term Memory, and the Model Context Protocol (MCP).*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Workflow-7B42BC?style=for-the-badge)](https://www.langchain.com/langgraph)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Memory-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20Database-DC244C?style=for-the-badge)](https://qdrant.tech/)
[![Redis](https://img.shields.io/badge/Redis-Background%20Queue-D82C20?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

</div>

---

## 🚀 Overview

SecondBrain AI is a **production-ready AI knowledge assistant** designed to transform personal documents into a searchable, conversational knowledge base.

Unlike a traditional chatbot, SecondBrain combines **Retrieval-Augmented Generation (RAG)**, **LangGraph-based agent orchestration**, **short-term and long-term memory**, and the **Model Context Protocol (MCP)** to create an extensible AI assistant capable of understanding documents, remembering context across conversations, and exposing its capabilities to external AI clients.

The project follows a modular architecture with asynchronous document ingestion, background processing, vector search using **Qdrant**, persistent conversational memory through **MongoDB**, and containerized deployment using **Docker Compose**.

---

## ✨ Key Highlights

- 🧠 Agentic RAG powered by **LangGraph**
- 📄 Upload and chat with PDF documents
- 🔍 Semantic vector search using **Qdrant**
- 🧠 Persistent long-term memory with **Mem0**
- 💬 Conversation state managed using **MongoDB Checkpointer**
- ⚡ FastAPI REST API
- 🔄 Redis + RQ background workers
- 🔌 Model Context Protocol (MCP) Server
- 🐳 Fully Dockerized architecture
- 📜 Structured logging and centralized error handling
- 🧪 Smoke-tested production workflow

---
# 📖 Project Overview

SecondBrain AI is a **production-ready personal knowledge assistant** that enables users to build an intelligent, searchable knowledge base from their own documents. Instead of relying solely on a large language model's built-in knowledge, SecondBrain retrieves relevant information from user-provided content and generates grounded, context-aware responses.

The system is built around an **Agentic Retrieval-Augmented Generation (RAG)** architecture powered by **LangGraph**. User requests are orchestrated through a multi-step workflow that performs intent routing, semantic retrieval, memory lookup, and response generation before returning a final answer.

To support real-world usage, SecondBrain combines multiple components into a modular backend:

- **FastAPI** for serving REST APIs
- **Qdrant** for semantic vector search
- **MongoDB** for conversation checkpoints and persistence
- **Mem0** for long-term memory management
- **Redis + RQ** for asynchronous background processing
- **Docker Compose** for reproducible deployment
- **Model Context Protocol (MCP)** for integration with external AI clients

The project follows production-oriented software engineering practices including modular architecture, centralized logging, environment-based configuration, containerization, background workers, and automated smoke testing.

Rather than being a simple chatbot, SecondBrain demonstrates how modern AI systems combine retrieval, reasoning, memory, orchestration, and external tools to build scalable intelligent applications.

---
# ✨ Features

## 🧠 AI & Intelligence

- Agentic Retrieval-Augmented Generation (RAG) powered by LangGraph
- Semantic document retrieval using Qdrant Vector Database
- Long-term memory using Mem0
- Short-term conversational memory with MongoDB Checkpointer
- Context-aware response generation using Google Gemini
- Multi-step workflow orchestration for intelligent query handling

---

## 📄 Document Processing

- PDF document ingestion
- Automatic text extraction and cleaning
- Intelligent document chunking
- Embedding generation
- Vector indexing for semantic search

---

## ⚙️ Backend & Infrastructure

- FastAPI REST API
- Asynchronous document processing using Redis + RQ
- Modular service-oriented architecture
- Centralized logging
- Custom exception handling
- Environment-based configuration
- Production-ready Docker deployment

---

## 🔌 Integrations

- Model Context Protocol (MCP) Server
- REST API endpoints
- Command Line Interface (CLI)

---

## 🧪 Quality & Reliability

- Smoke tests
- Dockerized development environment
- Persistent MongoDB storage
- Persistent Qdrant storage
- Modular project structure
---

# 🏗️ System Architecture

The following diagram illustrates the high-level architecture of SecondBrain AI.

<p align="center">
  <img src="assets/architecture-overview.png" alt="SecondBrain Architecture" width="100%">
</p>

SecondBrain follows a modular architecture where each component has a well-defined responsibility.

| Component | Responsibility |
|-----------|----------------|
| FastAPI | Exposes REST APIs |
| LangGraph | Orchestrates the AI workflow |
| Gemini | Generates responses |
| Qdrant | Stores vector embeddings |
| MongoDB | Stores conversation state |
| Mem0 | Manages long-term memory |
| Redis + RQ | Executes background jobs |
| MCP Server | Exposes tools for external AI clients |
---

# 🔄 Detailed Workflow

The following diagram illustrates the complete execution flow inside SecondBrain AI.

<p align="center">
  <img src="assets/architecture-detailed.png" alt="SecondBrain Detailed Workflow" width="100%">
</p>

## Request Flow

```text
User
   │
   ▼
FastAPI
   │
   ▼
LangGraph Workflow
   │
   ├── Route Request
   ├── Retrieve Documents
   ├── Retrieve Memory
   ├── Grade Documents
   ├── Rewrite Query (if needed)
   ├── Generate Response
   └── Store Conversation Memory
   │
   ▼
Gemini LLM
   │
   ▼
Response
```

## Document Upload Flow

```text
PDF Upload
     │
     ▼
FastAPI
     │
     ▼
Redis Queue
     │
     ▼
RQ Worker
     │
     ▼
PDF Loader
     │
     ▼
Text Cleaning
     │
     ▼
Chunking
     │
     ▼
Gemini Embeddings
     │
     ▼
Qdrant Vector Store
```

This architecture separates document ingestion from user interaction, enabling scalable background processing while keeping the API responsive.
---

# ⚙️ Tech Stack

| Category | Technologies |
|----------|--------------|
| **Programming Language** | Python 3.12 |
| **Backend Framework** | FastAPI |
| **AI Framework** | LangChain, LangGraph |
| **LLM** | Google Gemini |
| **Embeddings** | Gemini Embedding Model |
| **Vector Database** | Qdrant |
| **Memory** | Mem0, MongoDB Checkpointer |
| **Database** | MongoDB |
| **Background Processing** | Redis, RQ Worker |
| **Document Processing** | PyPDF |
| **API Documentation** | Swagger / OpenAPI |
| **Protocol** | Model Context Protocol (MCP) |
| **Containerization** | Docker, Docker Compose |
| **Configuration** | Python Dotenv |
| **Testing** | Smoke Tests |
| **Version Control** | Git, GitHub |
---

# 📂 Project Structure

```text
SecondBrain/
│
├── secondbrain/
│   ├── agent/              # Agent orchestration
│   ├── agents/             # Specialized AI agents
│   ├── api/                # FastAPI endpoints
│   ├── cli/                # Command-line interface
│   ├── core/               # Logging & exceptions
│   ├── graph/              # LangGraph workflow
│   ├── mcp_server/         # MCP server implementation
│   ├── memory/             # Short & long-term memory
│   ├── models/             # Request & response models
│   ├── queues/             # Redis queue & worker
│   ├── rag/                # RAG pipeline
│   ├── tools/              # AI tools
│   ├── data/               # Runtime data
│   └── main.py             # FastAPI application
│
├── tests/                  # Smoke tests
├── assets/                 # README images
├── logs/                   # Application logs
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 📦 Core Components

| Module | Description |
|---------|-------------|
| **RAG Pipeline** | Document ingestion, chunking, embeddings, retrieval |
| **LangGraph** | Agent workflow orchestration |
| **Memory** | Short-term & long-term conversational memory |
| **FastAPI** | REST API layer |
| **Redis Worker** | Background document processing |
| **Qdrant** | Vector similarity search |
| **MongoDB** | Conversation persistence |
| **MCP Server** | External AI tool integration |
---

# 🔬 Research Extensions

SecondBrain has four research extensions on top of the base agentic RAG system. They are
**additive and flag-gated**. The default `GRAPH_MODE=agent` runs the original two-node agent
graph unchanged, and `GRAPH_MODE=adaptive` enables the new graph in `secondbrain/graph/adaptive.py`.
Every component falls back to the old behaviour on error. Implementation details, deviations
from the design spec and known issues are in [`docs/IMPLEMENTATION_NOTES.md`](docs/IMPLEMENTATION_NOTES.md).

### P1 — Query-complexity router
**Problem:** every query, even "hi", goes through the same expensive multi-step agent loop.
**Solution:** `routing/classifier.py` labels each query `no_search` (answer directly), `simple`
(one retrieval and one generation) or `complex` (tool-calling agent). Regex heuristics run first,
and Gemini zero-shot classification is used only when the heuristics are unsure. Any failure
falls back to `complex`. *Scope note:* this replaces the fine-tuned T5 router from the proposal
with heuristics plus zero-shot classification. A trained router is future work.

### P2 — LO-MCP (latency-optimised tool selection)
**Problem:** every tool schema is injected into every LLM call, which costs tokens and latency.
**Solution:** `lomcp/` embeds each tool's description once and caches the schemas and vectors in
Redis (with an in-process fallback). It predicts the few tools a query needs and binds **only
those schemas** to the LLM (`search_documents` is always included). External MCP clients get the
same behaviour through the `discover_tools` meta-tool (tool-search pattern), because FastMCP
always lists every registered tool.

### P3 — AAM (Asynchronous Anti-drift Memory)
**Problem:** long-term memory drifts, and outdated facts stay and keep being retrieved.
**Solution:** when a session ends (`session_end: true` or the `end_session` MCP tool), a background
job extracts facts and finds similar memories. An LLM judge labels each pair `SAME / CONTRADICTS / UNRELATED`.
Contradicted memories are **deprecated** (not deleted) in a MongoDB status table, and recall filters
them out. Per-turn synchronous memory writes are removed from the request path. *Scope note:*
Mem0 already does some add/update/delete inference itself. AAM adds **auditable deprecation**
and moves the work off the hot path.

### P4 — Two-stage verification
**Problem:** hallucinations, cascading errors, and low-quality chunks that pollute retrieval.
**Solution:** **Stage 1 (ingestion)** runs `rag/processors/quality_filter.py`, which drops chunks
that are too short, have a low alphabetic ratio, look like a table of contents, or are duplicates,
and stores a `quality_score`. **Stage 2 (runtime)** runs `verification/confidence.py` and computes
a measured confidence `C = w1·s_top + w2·r + w3·g` (top similarity, share of relevant chunks,
groundedness check). Low confidence triggers **one retry** with a rewritten query, then the
system **abstains and flags the question for human review**. *Scope note:* stage 1 is heuristic.
The cross-encoder from the proposal is an optional add-on, because its cut-off must be calibrated
per corpus.

## Adaptive graph (`GRAPH_MODE=adaptive`)

```mermaid
flowchart TD
  S([START]) --> M[recall_memory]
  M --> C{classify}
  C -- no_search --> CH[chat]
  C -- simple --> R["retrieve (k = SIMPLE_K)"]
  C -- complex --> T["select_tools (LO-MCP)"]
  T --> A["agent (selected tools only)"]
  A -- tool calls --> TN[tools]
  TN --> A
  A -- done --> E[collect_evidence]
  R --> G[generate]
  G --> V{"verify (confidence + groundedness)"}
  E --> V
  V -- deliver --> F[finalize]
  V -- "retry once" --> W["rewrite (k = RETRY_K)"]
  W --> R
  V -- abstain --> AB["abstain + needs_review"]
  AB --> F
  CH --> F
  F --> X([END])
```

On the `complex` route, evidence is captured from the `search_documents` tool artifact, so
verification also runs on the agent path. The `no_search` route skips retrieval and verification.

## Feature flags

All flags live in `secondbrain/config.py` and are **read from the environment on every access**,
so the evaluation harness can switch configurations at runtime.

| Env var | Default | Meaning |
|---|---|---|
| `GRAPH_MODE` | `agent` | `agent` = legacy graph, `adaptive` = new graph |
| `FORCE_ROUTE` | *(empty)* | `no_search` \| `simple` \| `complex`: forces the route (used for baselines) |
| `ENABLE_ROUTER` | `1` | `0` → every query is `complex` |
| `ROUTER_MODE` | `hybrid` | `heuristic` \| `llm` \| `hybrid` |
| `SIMPLE_K` | `4` | chunks retrieved on the `simple` route |
| `RETRY_K` | `6` | chunks retrieved on the retry after a query rewrite |
| `MAX_AGENT_STEPS` | `4` | maximum agent ⇄ tools iterations on the `complex` route |
| `ENABLE_LOMCP` | `1` | `0` → all tools are bound |
| `LOMCP_TOP_K` | `3` | maximum number of predicted tools |
| `LOMCP_MARGIN` | `0.08` | keep tools within this similarity of the best match |
| `LOMCP_MIN_SIM` | `0.30` | minimum query–tool similarity |
| `LOMCP_ALWAYS_INCLUDE` | `search_documents` | comma-separated tools that are always bound |
| `ENABLE_VERIFY` | `1` | `0` → no confidence or grounding step |
| `VERIFY_SIMPLE_LLM` | `0` | `1` → also run the LLM groundedness check on the `simple` route |
| `CONF_W_RETRIEVAL` / `CONF_W_RELEVANCE` / `CONF_W_GROUNDED` | `0.30` / `0.20` / `0.50` | confidence weights w1 / w2 / w3 |
| `CONF_SCORE_REL_MIN` | `0.50` | similarity at which a chunk counts as relevant (for `r`) |
| `CONF_HIGH` / `CONF_MEDIUM` | `0.70` / `0.45` | label cut-offs |
| `CONF_ABSTAIN` | `0.30` | below this → retry, then abstain |
| `MAX_RETRIES` | `1` | query-rewrite retries before abstaining |
| `QUALITY_ENABLED` | `1` | ingestion quality filter |
| `QUALITY_MIN_CHARS` / `QUALITY_MIN_ALPHA` | `60` / `0.55` | quality-filter cut-offs |
| `ENABLE_AAM` | `1` | `0` → legacy per-turn memory save in `finalize` |
| `AAM_MODE` | `background` | `background` (FastAPI task) \| `queue` (RQ) \| `inline` |
| `AAM_SIM_THRESHOLD` / `AAM_MAX_FACTS` | `0.60` / `8` | memory-conflict candidate threshold / facts per session |

> The `CONF_*` and `LOMCP_*` defaults are **not calibrated**. Run `eval/calibrate.py` on your own
> documents before you switch production to `GRAPH_MODE=adaptive`.

## `/chat` contract

The request adds two optional fields, so existing clients keep working:

```json
POST /chat
{
  "query": "How many days of annual leave do I get?",
  "thread_id": 1,
  "user_id": "mandar",
  "session_end": false
}
```

`user_id` defaults to `str(thread_id)`. `session_end: true` triggers AAM reflection after the turn.

Example response on the `simple` route:

```json
{
  "answer": "You get 20 days of paid leave per year.",
  "confidence": "High",
  "confidence_score": 0.892,
  "route": "simple",
  "grounded": null,
  "abstained": false,
  "needs_review": false,
  "sources": [{"document": "hr_policy.pdf", "page": "3", "score": 0.82}],
  "metrics": {
    "t_memory_ms": 140.2, "t_classify_ms": 0.3, "t_retrieve_ms": 610.5,
    "t_generate_ms": 1350.8, "t_verify_ms": 0.1, "t_finalize_ms": 0.2,
    "latency_ms": 2115, "route_method": "heuristic", "retries": 0
  },
  "reflection": null
}
```

| Field | Values |
|---|---|
| `confidence` | `High` \| `Medium` \| `Low` (measured), `N/A` (no document evidence used, e.g. `no_search`), `Unverified` (verification disabled or `GRAPH_MODE=agent`) |
| `route` | `no_search` \| `simple` \| `complex` (`null` in legacy mode) |
| `grounded` | result of the LLM groundedness check, or `null` if it was skipped |
| `abstained` / `needs_review` | `true` when the system declined to answer after one retry |
| `metrics` | per-node timings, `latency_ms`, `route_method`, `retries`. On the `complex` route it also has `tools_selected`, `schema_tokens_full` and `schema_tokens_selected` |
| `reflection` | AAM scheduling result when `session_end` is `true` (e.g. `{"status": "scheduled"}`) |

## Ablation matrix

| Config | env |
|---|---|
| **A — Naive RAG** | `GRAPH_MODE=adaptive FORCE_ROUTE=simple ENABLE_VERIFY=0 ENABLE_LOMCP=0 ENABLE_AAM=0` |
| **B — Standard agentic RAG** | `GRAPH_MODE=adaptive FORCE_ROUTE=complex ENABLE_VERIFY=0 ENABLE_LOMCP=0 ENABLE_AAM=0` |
| **Full system** | `GRAPH_MODE=adaptive` (all defaults) |
| Full − router | `FORCE_ROUTE=complex` |
| Full − LO-MCP | `ENABLE_LOMCP=0` |
| Full − AAM | `ENABLE_AAM=0` |
| Full − verification | `ENABLE_VERIFY=0` |

## Tests and evaluation

Offline unit and graph tests (no network, no API key; Python 3.12):

```bash
pip install -r requirements-dev.txt && pytest -q
```

`tests/smoke_test.py` is a separate **live** integration script. It needs a real `GOOGLE_API_KEY`,
Qdrant, MongoDB and Mem0. Run it with `python tests/smoke_test.py`.

The evaluation harness reads `eval/data/queries.jsonl` (one `{"id", "query", "label", "answerable", "gold"}`
object per line) and `eval/data/memory_conflicts.jsonl`. The committed files are small samples; replace them
with ~100 queries and ≥30 conflict pairs built from your own documents:

```bash
# 1. calibrate the confidence thresholds (answerable vs unanswerable top-1 scores)
python -m eval.calibrate eval/data/queries.jsonl

# 2. run the ablation configs (all configs if none are named)
python -m eval.run_eval eval/data/queries.jsonl out/results.csv [config ...]
#    configs: A_naive B_agentic full full_no_router full_no_lomcp full_no_verify full_no_aam

# 3. P2 scaling: LO-MCP against a simulated 40-tool registry (embeddings only)
python -m eval.lomcp_scaling out/lomcp_scaling.csv

# 4. P3 stale-fact rate, baseline vs AAM
ENABLE_AAM=0 python -m eval.memory_drift eval/data/memory_conflicts.jsonl out/drift_base.csv
ENABLE_AAM=1 python -m eval.memory_drift eval/data/memory_conflicts.jsonl out/drift_aam.csv
```

The Gemini free tier allows only 20 `gemini-2.5-flash` requests per day, which is not enough for a full
ablation run (7 configs × ~100 queries × 1–4 LLM calls). Use a paid key or run configs on separate days.

---

# 🚀 Installation & Quick Start

## Prerequisites

Before getting started, ensure you have the following installed:

- Python 3.12 (pinned in `runtime.txt` and the `Dockerfile`)
- Docker & Docker Compose
- Git
- Google Gemini API Key

---

## Clone the Repository

```bash
git clone https://github.com/MandarGavali/SecondBrain.git
cd SecondBrain
```

---

## Configure Environment Variables

Create a `.env` file in the project root.

```env
GOOGLE_API_KEY=your_google_api_key

MONGODB_URI=mongodb://localhost:27017
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
```

---

## Run with Docker (Recommended)

Start the complete application stack:

```bash
docker compose up --build
```

This launches:

- FastAPI Server
- Redis
- MongoDB
- Qdrant
- Background Worker

Swagger UI:

```
http://localhost:8000/docs
```

---

## Run Locally (Without Docker)

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn secondbrain.main:app --reload
```

Start the Redis worker in another terminal:

```bash
python -m secondbrain.queues.worker
```

The API will be available at:

```
http://localhost:8000
```

Swagger UI:

```
http://localhost:8000/docs
```
---

# 🐳 Docker Deployment

SecondBrain is fully containerized using Docker Compose, making the entire application stack reproducible with a single command.

## Containers

| Container | Purpose |
|-----------|---------|
| `secondbrain-api` | FastAPI application |
| `secondbrain-worker` | Background document processing |
| `secondbrain-mongodb` | Conversation state & memory |
| `secondbrain-qdrant` | Vector database |
| `secondbrain-redis` | Background job queue |

---

## Start the Stack

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up -d
```

Stop the stack:

```bash
docker compose down
```

Rebuild after dependency changes:

```bash
docker compose up --build --force-recreate
```

---

## Verify Services

```bash
docker ps
```

Expected running containers:

- secondbrain-api
- secondbrain-worker
- secondbrain-mongodb
- secondbrain-qdrant
- secondbrain-redis

---

## Persistent Storage

Docker volumes are used to persist application data.

| Volume | Stores |
|---------|--------|
| `mongodb_data` | MongoDB data |
| `qdrant_data` | Vector embeddings |

This ensures conversations and indexed documents remain available even after restarting the containers.
---

# 📡 API Reference

Once the application is running, Swagger documentation is available at:

```
http://localhost:8000/docs
```

<p align="center">
  <img src="assets/swagger-ui.png" alt="Swagger UI" width="100%">
</p>

## REST Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| **POST** | `/upload` | Upload and index PDF documents |
| **POST** | `/chat` | Chat with indexed documents |
| **GET** | `/jobs/{job_id}` | Check background processing status |
| **GET** | `/healthz` | Liveness check (`{"status": "ok"}`) |

---

## Example Upload Request

```bash
curl -X POST \
  "http://localhost:8000/upload" \
  -F "file=@document.pdf"
```

---

## Example Chat Request

```json
POST /chat

{
  "query": "Summarize the uploaded document."
}
```
---

# 🔌 Model Context Protocol (MCP) Integration

SecondBrain includes a dedicated **Model Context Protocol (MCP) Server**, allowing external AI clients (such as Claude Desktop, Cursor, VS Code, and other MCP-compatible applications) to interact directly with the knowledge base.

Instead of exposing only REST APIs, MCP enables AI assistants to invoke tools, retrieve documents, and access memory through a standardized protocol.

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `ask_secondbrain` | Query the complete RAG pipeline with memory support |
| `search_documents` | Perform semantic search across indexed documents |
| `upload_document` | Upload new documents to the knowledge base |
| `memory` | Access and manage long-term memory |
| `end_session` | Mark a conversation as finished so long-term memory is reconciled in the background (AAM) |
| `discover_tools` | Describe a task; returns only the schemas of the tools relevant to it (LO-MCP tool search) |

---

## MCP Capabilities

- AI-assisted document search
- Agentic RAG workflow execution
- Long-term memory retrieval
- Knowledge base interaction
- Tool-based AI integration
- Standardized MCP interface

---

## MCP Architecture

```text
AI Client
(Claude Desktop / Cursor / VS Code)
            │
            ▼
      MCP Server
            │
            ▼
    SecondBrain Tools
            │
            ▼
 LangGraph Workflow
            │
     ┌──────┴────────┐
     ▼               ▼
 MongoDB         Qdrant
     │               │
     └──────┬────────┘
            ▼
      Google Gemini
```

The MCP server allows external AI systems to securely access the capabilities of SecondBrain without directly interacting with the internal application components.
---

# 🖼️ Screenshots

## System Architecture

<p align="center">
  <img src="assets/architecture-overview.png" width="100%">
</p>

---

## Engineering Workflow

<p align="center">
  <img src="assets/architecture-detailed.png" width="100%">
</p>

---

## FastAPI Swagger UI

<p align="center">
  <img src="assets/swagger-ui.png" width="100%">
</p>

---

# 🚧 Future Improvements

SecondBrain is designed with extensibility in mind. Some planned enhancements include:

- 🌐 Web-based user interface
- 🔐 User authentication and role-based access control
- 📚 Support for additional document formats (DOCX, Markdown, HTML, TXT)
- ☁️ Cloud storage integration (AWS S3, Google Cloud Storage)
- 🔍 Hybrid Search (Semantic + Keyword Search)
- ⚡ Streaming responses using Server-Sent Events (SSE)
- 📈 Observability with Prometheus & Grafana
- 📊 Monitoring and analytics dashboard
- 🧩 Plugin architecture for custom tools
- 🤖 Multi-agent collaboration workflows
- 🗣 Voice input and speech synthesis
- 🌍 Multi-language document support
- 📱 Web and mobile client applications
- 🚀 Kubernetes deployment for horizontal scaling

---

# 🤝 Contributing

Contributions are welcome!

If you'd like to improve SecondBrain, please follow these steps:

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/your-feature
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push to your branch

```bash
git push origin feature/your-feature
```

5. Open a Pull Request

Please ensure your code follows the existing project structure and coding style.

---

# 📄 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for more information.

---

# 🙏 Acknowledgements

This project was built using several outstanding open-source technologies.

Special thanks to the teams behind:

- LangChain
- LangGraph
- Google Gemini
- FastAPI
- Qdrant
- MongoDB
- Redis
- Mem0
- Docker
- Model Context Protocol (MCP)

Their work makes projects like SecondBrain possible.

---

<div align="center">

## ⭐ If you found this project interesting, consider giving it a star!

**Built with ❤️ by [Mandar Gavali](https://github.com/MandarGavali)**

</div>