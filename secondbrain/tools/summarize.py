from langchain_core.prompts import ChatPromptTemplate

from secondbrain.tools.search import search_documents
from secondbrain.rag.llm.gemini_llm import get_llm
from secondbrain.utils.exceptions import GenerationError, RetrievalError
from secondbrain.utils.logger import logger

def summarize_documents(query: str, k: int = 10) -> str:
    """
    Summarizes knowledge retrieved from the indexed documents based on the given query.

    Retrieves the top-k relevant documents and uses the Gemini LLM to generate a factual,
    concise, and comprehensive summary grounded entirely in the retrieved context.

    Args:
        query (str): The subject or question to summarize.
        k (int, optional): The number of relevant documents to retrieve. Defaults to 10.

    Returns:
        str: A factual summary of the retrieved context, or a helpful message if no 
             documents are found.

    Raises:
        ValueError: If the query is empty or blank.
        RetrievalError: If document retrieval fails.
        GenerationError: If LLM summary generation fails.
    """
    logger.info(f"summarize_documents tool invoked with query='{query}' and k={k}")
    
    # 1. Retrieve Documents
    documents = search_documents(query=query, k=k)
    
    if not documents:
        return "No relevant documents were found to summarize. Please try adjusting your query."
    
    # 2. Combine Context
    context = "\n\n".join([
        f"--- Source: {doc.metadata.get('source', 'Unknown')} (Page {doc.metadata.get('page_label', 'N/A')}) ---\n"
        f"{doc.page_content}"
        for doc in documents
    ])
    
    # 3. Formulate Prompt
    system_prompt = """
You are a highly skilled summarization assistant.
Your task is to summarize the provided context concisely and comprehensively.

STRICT RULES:
1. Be highly factual and preserve key concepts.
2. Remove redundancy and repetition.
3. NEVER hallucinate or invent information outside of the provided context.
4. If the context does not contain enough information to make a good summary about the query, state that explicitly.
5. Provide the summary in a clear, easy-to-read format (e.g., bullet points or concise paragraphs).
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Query to summarize: {query}\n\nContext:\n{context}")
    ])
    
    # 4. Generate Summary using Gemini
    try:
        llm = get_llm()
        chain = prompt | llm
        
        logger.info("Invoking Gemini LLM for summarization...")
        response = chain.invoke({"query": query, "context": context})
        
        logger.info("Successfully generated summary.")
        return response.content
        
    except Exception as e:
        logger.exception(f"Error occurred during summary generation: {e}")
        raise GenerationError(f"Failed to generate summary: {e}") from e
