from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition

from secondbrain.graph.agent_node import agent_node
from secondbrain.graph.checkpointer import get_checkpointer
from secondbrain.graph.state import AgentState
from secondbrain.graph.tool_node import tool_node


def create_graph():
    """Legacy SecondBrain agent (GRAPH_MODE=agent): agent <-> tools loop."""
    builder = StateGraph(AgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=get_checkpointer())
