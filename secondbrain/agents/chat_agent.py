from secondbrain.utils.logger import logger
from secondbrain.utils.exceptions import GenerationError
from secondbrain.rag.services.chat_service import generate_standard_chat

def run_chat_agent(query: str, history: list = None) -> str:
    """
    Agentic wrapper for standard chat answer generation.
    
    FIX: Accepts conversation history from the graph state (restored via MongoDB
    checkpoint) and threads it through to the LLM so prior turns are visible.
    """
    try:
        # FIX: Pass history so memory checkpoint is actually used by the LLM.
        answer = generate_standard_chat(query=query, history=history)
        return answer
    except Exception as e:
        logger.error("Chat agent failed to produce an answer.")
        raise GenerationError(f"Failed to generate chat answer: {e}") from e
