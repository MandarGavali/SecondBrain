from typing import Dict, Any

from secondbrain.utils.logger import logger
from secondbrain.utils.exceptions import ValidationError, GraphExecutionError
from secondbrain.graph.state import GraphState
from secondbrain.agents.retrieval_agent import run_retrieval_agent
from secondbrain.agents.generation_agent import run_generation_agent
from secondbrain.rag.services.document_grading_service import grade_documents
from secondbrain.rag.services.query_rewriter_service import rewrite_query
from langchain_core.messages import HumanMessage, AIMessage

def retrieve_node(state: GraphState) -> Dict[str, Any]:
    """Node responsible for retrieving documents based on the user query."""
    # 1. Validate State
    query = state.get("rewritten_query")

    if query is None:
        query = state["user_query"]

    if not query:
        logger.error("Missing 'user_query' in state.")
        raise ValidationError("The 'user_query' is required to execute retrieve_node.")

    # 2. Log Start
    logger.info(f"Executing retrieve_node for query: '{query}'")

    try:
        # 3. Execute Business Service (via Agent)
        documents = run_retrieval_agent(query=query, k=5)
        
        # 4. Log Success
        logger.info(f"retrieve_node completed successfully. Retrieved {len(documents)} documents.")
        
        # TESTING LOGGING
        logger.info("\n" + "="*50)
        logger.info("NODE : RETRIEVE")
        logger.info("===============\n")
        logger.info("Query used for retrieval:")
        logger.info(f"{query}\n")
        logger.info("Number of retrieved documents:")
        logger.info(f"{len(documents)}\n")
        logger.info("Page numbers:")
        logger.info(f"{[doc.metadata.get('page_label', 'N/A') for doc in documents]}\n")
        logger.info("Source filenames:")
        logger.info(f"{[doc.metadata.get('source', 'N/A') for doc in documents]}\n")
        logger.info("="*50 + "\n")
        
        # 5. Return State Update
        return {
            "retrieved_docs": documents
        }
    except Exception as e:
        # 6. Handle Exceptions
        logger.exception("retrieve_node execution failed.")
        raise GraphExecutionError(f"retrieve_node failed: {e}") from e

def generate_node(state: GraphState) -> Dict[str, Any]:
    """Node responsible for generating an answer based on retrieved documents."""
    # 1. Validate State
    query = state.get("user_query")
    documents = state.get("filtered_docs")
    
    if not query:
        logger.error("Missing 'user_query' in state.")
        raise ValidationError("The 'user_query' is required to execute generate_node.")
    
    if documents is None:
        logger.error("Missing 'retrieved_docs' in state.")
        raise ValidationError("The 'retrieved_docs' are required to execute generate_node.")

    # 2. Log Start
    logger.info("Executing generate_node.")

    try:
        # 3. Execute Business Service (via Agent)
        answer = run_generation_agent(query=query, documents=documents)
        
        # 4. Log Success
        logger.info("generate_node completed successfully.")
        
        # TESTING LOGGING
        logger.info("\n" + "="*50)
        logger.info("NODE : GENERATE")
        logger.info("===============\n")
        logger.info("Number of context documents:")
        logger.info(f"{len(documents)}\n")
        logger.info("First 150 characters of generated answer:")
        logger.info(f"{answer[:150]}...\n")
        logger.info("Conversation Length:")
        msg_len = len(state.get("messages", [])) + 2
        logger.info(f"{msg_len}\n")
        logger.info("="*50 + "\n")
        
        # 5. Return State Update
        return {
            "answer": answer,

            "messages": [
              HumanMessage(
                content=state["user_query"]
              ),

              AIMessage(
                content = answer
              )
            ]
        }
    except Exception as e:
        # 6. Handle Exceptions
        logger.exception("generate_node execution failed.")
        raise GraphExecutionError(f"generate_node failed: {e}") from e


from secondbrain.agents.chat_agent import run_chat_agent

def router_node(state: GraphState) -> Dict[str, Any]:
    """Node responsible for routing queries between RAG and standard chat."""
    # 1. Validate State
    query = state.get("user_query")
    if not query:
        logger.error("Missing 'user_query' in state.")
        raise ValidationError("The 'user_query' is required to execute router_node.")

    # 2. Log Start
    logger.info("Executing router_node.")

    try:
        # 3. Execute Business Logic
        query_lower = query.lower()
        rag_keywords = [
            "document", "pdf", "chapter", "project", 
            "summarize", "explain", "according", "notes"
        ]

        route = "chat"
        for keyword in rag_keywords:
            if keyword in query_lower:
                route = "rag"
                break
                
        # 4. Log Success
        logger.info(f"router_node decided route: '{route}'")
        
        # TESTING LOGGING
        logger.info("\n" + "="*50)
        logger.info("NODE : ROUTER")
        logger.info("=============\n")
        logger.info("Incoming Query:")
        logger.info(f"{query}\n")
        logger.info("Selected Route:")
        logger.info(f"{route}\n")
        logger.info("="*50 + "\n")
        
        # 5. Return State Update
        return {
            "route": route
        }
    except Exception as e:
        # 6. Handle Exceptions
        logger.exception("router_node execution failed.")
        raise GraphExecutionError(f"router_node failed: {e}") from e

def chat_node(state: GraphState) -> Dict[str, Any]:
    """Node responsible for general chat when RAG is not needed."""
    # 1. Validate State
    query = state.get("user_query")
    if not query:
        logger.error("Missing 'user_query' in state.")
        raise ValidationError("The 'user_query' is required to execute chat_node.")

    # 2. Log Start
    logger.info("Executing chat_node.")

    try:
        # FIX: Pass existing messages from the checkpoint so the LLM has
        # conversational context from previous turns in this thread.
        existing_messages = state.get("messages", [])
        logger.info(f"Executing chat_node with {len(existing_messages)} prior messages.")
        answer = run_chat_agent(query=query, history=existing_messages)
        
        # 4. Log Success
        logger.info("chat_node completed successfully.")
        
        # TESTING LOGGING
        logger.info("\n" + "="*50)
        logger.info("NODE : CHAT")
        logger.info("===========\n")
        logger.info("User Query:")
        logger.info(f"{query}\n")
        logger.info("Generated Response Preview:")
        logger.info(f"{answer[:150]}...\n")
        logger.info("Conversation Length:")
        msg_len = len(existing_messages) + 2
        logger.info(f"{msg_len}\n")
        logger.info("="*50 + "\n")

        # 5. Return State Update
        return {
            "answer": answer,
            "messages": [
                HumanMessage(content=state["user_query"]),
                AIMessage(content=answer)
            ]
        }
    except Exception as e:
        # 6. Handle Exceptions
        logger.exception("chat_node execution failed.")
        raise GraphExecutionError(f"chat_node failed: {e}") from e

def grade_documents_node(state: GraphState):
    # FIX: Use .get() with a safe default to avoid KeyError if retrieved_docs
    # is missing from state (e.g., if the retrieve node failed silently).
    retrieved = state.get("retrieved_docs", [])

    documents = grade_documents(
        query=state["user_query"],
        documents=retrieved
    )

    # TESTING LOGGING
    logger.info("\n" + "="*50)
    logger.info("NODE : DOCUMENT GRADER")
    logger.info("======================\n")
    logger.info("Retrieved document count:")
    logger.info(f"{len(state.get('retrieved_docs', []))}\n")
    logger.info("Filtered document count:")
    logger.info(f"{len(documents)}\n")
    logger.info("Pages that survived filtering:")
    logger.info(f"{[doc.metadata.get('page_label', 'N/A') for doc in documents]}\n")
    logger.info("="*50 + "\n")

    return {
        "filtered_docs": documents
    }

def rewrite_query_node(state: GraphState):

    current_query = state.get("rewritten_query") or state["user_query"]

    rewritten = rewrite_query(current_query)  

    # TESTING LOGGING
    logger.info("\n" + "="*50)
    logger.info("NODE : QUERY REWRITER")
    logger.info("=====================\n")
    logger.info("Original Query:")
    logger.info(f"{current_query}\n")
    logger.info("Rewritten Query:")
    logger.info(f"{rewritten}\n")
    logger.info("Retry Count:")
    logger.info(f"{state.get('retries', 0) + 1}\n")
    logger.info("="*50 + "\n")

    return {
        "rewritten_query": rewritten,
        "retries": state.get("retries", 0) + 1
    }

from secondbrain.rag.services.hallucination_checker_service import check_hallucination

def check_hallucination_node(state: GraphState):
    """
    Node responsible for checking if the generated answer is grounded in the retrieved documents.
    """
    logger.info("Executing check_hallucination_node.")
    
    answer = state.get("answer", "")
    documents = state.get("filtered_docs") or state.get("retrieved_docs", [])
    
    is_grounded, reason = check_hallucination(answer=answer, documents=documents)
    
    logger.info(f"Hallucination Check: is_grounded={is_grounded}, reason='{reason}'")
    
    # TESTING LOGGING
    logger.info("\n" + "="*50)
    logger.info("NODE : HALLUCINATION CHECKER")
    logger.info("============================\n")
    logger.info("Grounded:")
    logger.info(f"{is_grounded}\n")
    logger.info("Reason:")
    logger.info(f"{reason}\n")
    logger.info("="*50 + "\n")
    
    return {
        "is_grounded": is_grounded,
        "verification_reason": reason
    }