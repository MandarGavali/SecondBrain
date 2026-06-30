from typing import List
from langchain_core.documents import Document

from secondbrain.utils.logger import logger
from secondbrain.utils.exceptions import GenerationError
from secondbrain.rag.llm.gemini_llm import generate_answer

def generate_grounded_answer(query: str, documents: List[Document]) -> str:
    """
    Accepts retrieved documents, builds the context string, and calls the LLM
    to generate an answer grounded in the provided context.
    This separates context building from both the orchestrator and the LLM client.
    """
    logger.info(f"Generating answer for query: '{query}' using {len(documents)} documents.")
    try:
        # Build Context from the retrieved documents
        context = "\n\n\n".join(
            [
                f"Page Content: {doc.page_content}\n"
                f"Page Number: {doc.metadata.get('page_label', 'N/A')}\n"
                f"File Location: {doc.metadata.get('source', 'N/A')}"
                for doc in documents
            ]
        )

        # Call Gemini LLM logic
        answer = generate_answer(query=query, context=context)
        logger.info("Successfully generated answer.")
        return answer
    except Exception as e:
        logger.exception("Error occurred during answer generation.")
        raise GenerationError(f"Answer generation failed: {e}") from e
