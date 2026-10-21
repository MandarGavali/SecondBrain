> **LEGACY:** these wrappers belong to the earlier corrective-RAG graph (`secondbrain/graph/nodes.py`) and are not used by the running agent graph (`secondbrain/graph/workflow.py:create_graph`).

# Agents Layer

This directory acts as the orchestration boundary for AI reasoning. 

While currently serving as structural wrappers around the business services (`rag/services/`), this layer is designed to eventually house:
- Query Routers
- Document Graders
- Query Rewriters
- Hallucination Checkers

## Dependency Direction
Graph -> Agents -> Services -> Infrastructure
