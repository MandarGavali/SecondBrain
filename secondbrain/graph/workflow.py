# from langgraph.graph import StateGraph, START, END

# from graph.state import GraphState
# from graph.nodes import (
#     router_node,
#     chat_node,
#     retrieve_node,
#     grade_documents_node,
#     generate_node,
#     rewrite_query_node,
#     check_hallucination_node
# )
# from graph.checkpointer import get_checkpointer


# def route_query(state: GraphState):
#     return state["route"]

# def grade_decision(state: GraphState):

#     if len(state["filtered_docs"]) >= 2:

#         return "generate"

#     if state["retries"] >= 1:

#         return "generate"

#     return "rewrite"


# def hallucination_decision(state: GraphState):
#     if state["is_grounded"]:
#         return "useful"
    
#     if state.get("retries", 0) >= 1:
#         return "useful"

#     return "not supported"

# graph_builder = StateGraph(GraphState)

# # Register Nodes
# graph_builder.add_node("router", router_node)
# graph_builder.add_node("chat", chat_node)
# graph_builder.add_node("retrieve", retrieve_node)
# graph_builder.add_node("generate", generate_node)
# graph_builder.add_node("grade_documents",grade_documents_node)
# graph_builder.add_node("rewrite_query",rewrite_query_node)
# graph_builder.add_node("check_hallucination", check_hallucination_node)

# # Start
# graph_builder.add_edge(START, "router")

# # Conditional Routing
# graph_builder.add_conditional_edges(
#     "router",
#     route_query,
#     {
#         "rag": "retrieve",
#         "chat": "chat"
#     }
# )



# # RAG Path
# graph_builder.add_edge("retrieve", "grade_documents")

# graph_builder.add_conditional_edges(
#   "grade_documents",
#   grade_decision,
#   {
#     "generate": "generate",
#     "rewrite": "rewrite_query"
#   }
# )

# graph_builder.add_edge("rewrite_query","retrieve")

# graph_builder.add_edge("generate", "check_hallucination")

# graph_builder.add_conditional_edges(
#     "check_hallucination",
#     hallucination_decision,
#     {
#         "useful": END,
#         "not supported": "generate"
#     }
# )
# # Chat Path
# graph_builder.add_edge("chat", END)


# # Compile LAST
# graph = graph_builder.compile()


# #
# def compile_graph_with_checkpointer():
#   checkpointer = get_checkpointer()

#   return graph_builder.compile(
#     checkpointer=checkpointer
#   )



from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import tools_condition

from secondbrain.graph.agent_node import agent_node
from secondbrain.graph.tool_node import tool_node


from secondbrain.graph.checkpointer import get_checkpointer
from secondbrain.graph.state import AgentState

def create_graph():
    """
    Creates and compiles the LangGraph workflow
    for the SecondBrain AI Agent.
    """

    builder = StateGraph(AgentState)

    # Nodes
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_node)

    # Start
    builder.add_edge(START, "agent")

    # Conditional Routing
    builder.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    # Tool Loop
    builder.add_edge("tools", "agent")

    checkpointer = get_checkpointer()
    return builder.compile(checkpointer=checkpointer)


# graph = create_graph()

