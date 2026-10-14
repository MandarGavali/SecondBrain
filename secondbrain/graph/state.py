# defines what data flows through the graph

from typing import Annotated, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    user_id: str


class AdaptiveState(TypedDict, total=False):
    """State for the adaptive graph (GRAPH_MODE=adaptive).

    NOTE: this state is persisted per thread by the Mongo checkpointer, so every per-turn field is
    reset by `new_turn_input()` at the start of each turn.
    """
    messages: Annotated[list, add_messages]
    user_id: str
    user_query: str
    rewritten_query: Optional[str]
    route: Optional[str]            # no_search | simple | complex
    route_method: Optional[str]     # heuristic | llm | fallback | forced | disabled
    memory_context: str
    selected_tools: list            # LO-MCP output (tool names)
    agent_steps: int
    evidence: list                  # [{text,page,document,source,chunk_id,score}]
    answer: Optional[str]
    retries: int
    is_grounded: Optional[bool]
    verification_reason: Optional[str]
    confidence_score: Optional[float]
    confidence_label: Optional[str]
    abstained: bool
    needs_review: bool
    metrics: dict
