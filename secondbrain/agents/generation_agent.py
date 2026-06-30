from typing import List
from langchain_core.documents import Document

from secondbrain.utils.logger import logger
from secondbrain.utils.exceptions import GenerationError
from secondbrain.rag.services.generation_service import generate_grounded_answer

def run_generation_agent(query: str, documents: List[Document]) -> str:
    """
    Agentic wrapper for answer generation.
    Currently simply delegates to the generation service, but will eventually
    house hallucination checking, self-correction, and grading logic.
    """
    try:
        answer = generate_grounded_answer(query=query, documents=documents)
        return answer
    except Exception as e:
        logger.error("Generation agent failed to produce an answer.")
        raise GenerationError(f"Failed to generate answer: {e}") from e
