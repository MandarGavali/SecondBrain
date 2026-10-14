# defines what data flows through the graph

from typing import Annotated, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    user_id: str


class GraphState(TypedDict):

  # Conversation memory — add_messages reducer appends rather than overwrites.
  # This is what LangGraph uses to persist history via the checkpointer.
  messages: Annotated[list, add_messages]

  user_query: str

  # Set by the rewrite node; retrieve_node prefers this over user_query if present.
  rewritten_query: Optional[str]

  retrieved_docs: Optional[list]

  # Set by grade_documents_node; fallback to retrieved_docs if empty.
  filtered_docs: Optional[list]

  answer: Optional[str]

  route: Optional[str]

  # Counts how many times the query has been rewritten. Guards against infinite loops.
  retries: int

  # Set by the hallucination checker.
  is_grounded: Optional[bool]

  verification_reason: Optional[str]


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
