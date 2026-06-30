# Future Improvements Roadmap

The Phase 4 architecture provides a highly stable foundation. Moving forward into future phases, the following enhancements should be considered to push the project toward an enterprise-grade standard.

## 1. Advanced Agent Features
- **Parallel Tool Execution:** LangChain natively supports executing multiple tool calls concurrently. Updating the `ToolNode` to run requests asynchronously could drastically reduce latency when searching and summarizing simultaneously.
- **Human-in-the-Loop Approval:** For destructive actions or deep research requests, implementing a conditional breakpoint in LangGraph to await user CLI/API approval would add a layer of safety.
- **Multi-Tool Reasoning:** Integrating advanced reasoning frameworks (like ReAct or Plan-and-Solve) over the standard functional-calling agent would improve handling of ambiguous, multi-step queries.

## 2. Infrastructure & Operations
- **Streaming Responses:** Implementing FastAPI WebSockets alongside LangGraph's streaming capabilities would allow the frontend to render LLM responses character-by-character, greatly improving perceived latency.
- **Better Observability:** Integrating LangSmith or an OpenTelemetry provider to visually trace the exact path of the LangGraph execution, tool usage duration, and LLM token usage.
- **Monitoring & Alerts:** Attach Prometheus/Grafana or Datadog metrics to the API endpoints to capture 429 API rate limits or MongoDB connection drops proactively.
- **Docker Improvements:** Containerizing Qdrant, MongoDB, and the FastAPI server into a unified `docker-compose.yml` for isolated, 1-click deployments.
- **Authentication & Tool Permissions:** Wrapping tool execution with specific JWT claims to restrict capabilities (e.g., standard users can search, but only admins can wipe documents).

## 3. Knowledge & Context
- **Source Citations Formatting:** Enhance the agent to return clickable hyperlinks or distinct UI metadata markers indicating exactly which paragraph generated the information, preventing hallucination masking.
- **Better Memory Management:** Implement LangGraph memory summarization to prevent context windows from expanding infinitely during long, multi-turn chat threads.

## 4. Testing & CI/CD
- **Unit and Integration Tests:** Adopt `pytest` for all underlying services with rigorous mocking (similar to the Phase 4 validation tests) to run natively in a GitHub Actions CI pipeline on every Pull Request.
- **Evaluation Framework:** Integrate an evaluation suite (like Ragas) to automatically score the quality of retrieved contexts against human-written ground truths.
