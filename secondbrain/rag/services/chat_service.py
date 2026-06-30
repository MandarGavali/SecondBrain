from secondbrain.utils.logger import logger
from secondbrain.utils.exceptions import GenerationError
from secondbrain.rag.llm.gemini_llm import generate_chat_response

def generate_standard_chat(query: str, history: list = None) -> str:
    """
    Service for standard chat responses without RAG context.
    
    FIX: Accepts conversation history (restored from MongoDB checkpoint) and
    passes it to the LLM so prior turns are visible to the model.
    """
    logger.info(f"Generating standard chat response for query: '{query}'")
    try:
        # FIX: Pass history so the LLM can see prior conversation turns.
        answer = generate_chat_response(query=query, history=history)
        logger.info("Successfully generated chat response.")
        return answer
    except Exception as e:
        logger.exception("Error occurred during chat generation.")
        raise GenerationError(f"Chat generation failed: {e}") from e
