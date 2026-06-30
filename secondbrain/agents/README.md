# Agents Layer

This directory acts as the orchestration boundary for AI reasoning. 

While currently serving as structural wrappers around the business services (`rag/services/`), this layer is designed to eventually house:
- Query Routers
- Document Graders
- Query Rewriters
- Hallucination Checkers

## Dependency Direction
Graph -> Agents -> Services -> Infrastructure
