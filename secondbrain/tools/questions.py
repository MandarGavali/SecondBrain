from langchain_core.prompts import ChatPromptTemplate

from secondbrain.tools.search import search_documents
from secondbrain.rag.llm.gemini_llm import get_llm
from secondbrain.utils.exceptions import GenerationError, RetrievalError
from secondbrain.utils.logger import logger

def generate_questions(query: str, difficulty: str = "mixed", num_questions: int = 10) -> str:
    """
    Generates interview-style questions using the indexed knowledge base.

    Retrieves relevant context based on the query and uses the Gemini LLM to generate
    questions (and concise answers) grounded exclusively in that context.

    Args:
        query (str): The subject area to generate questions for.
        difficulty (str, optional): The difficulty level of the questions. 
                                    Supported values: "easy", "medium", "hard", "mixed". 
                                    Defaults to "mixed".
        num_questions (int, optional): The exact number of questions to generate. Defaults to 10.

    Returns:
        str: A formatted string containing the generated questions and concise answers, 
             or a helpful message if no relevant context could be found.

    Raises:
        ValueError: If query is blank, difficulty is invalid, or num_questions <= 0.
        RetrievalError: If document retrieval fails.
        GenerationError: If LLM question generation fails.
    """
    logger.info(f"generate_questions tool invoked: query='{query}', difficulty='{difficulty}', num_questions={num_questions}")
    
    # 1. Parameter Validation
    valid_difficulties = {"easy", "medium", "hard", "mixed"}
    if difficulty.lower() not in valid_difficulties:
        raise ValueError(f"Invalid difficulty '{difficulty}'. Must be one of: {valid_difficulties}")
    if num_questions <= 0:
        raise ValueError(f"num_questions must be a positive integer, got {num_questions}")
    
    # 2. Retrieve Documents
    documents = search_documents(query=query, k=15)
    
    if not documents:
        return "No relevant documents were found to generate questions from. Please try adjusting your topic."
    
    # 3. Combine Context
    context = "\n\n".join([
        f"--- Source: {doc.metadata.get('source', 'Unknown')} (Page {doc.metadata.get('page_label', 'N/A')}) ---\n"
        f"{doc.page_content}"
        for doc in documents
    ])
    
    # 4. Formulate Prompt
    difficulty_instruction = {
        "easy": "Generate fundamental, conceptual questions suitable for beginners.",
        "medium": "Generate application-based and moderately complex questions.",
        "hard": "Generate advanced, scenario-based, and highly analytical questions.",
        "mixed": "Create a progressive difficulty sequence (Easy -> Medium -> Hard)."
    }.get(difficulty.lower(), "")

    system_prompt = f"""
You are an expert interviewer creating an assessment based strictly on the provided context.
Your task is to generate exactly {{num_questions}} interview questions.

STRICT RULES:
1. Stay 100% grounded in the retrieved context. NEVER hallucinate or use outside knowledge.
2. Produce conceptual and practical questions relevant to the context.
3. Generate EXACTLY {{num_questions}} questions. Number them clearly (1 to {{num_questions}}).
4. Difficulty constraint: {difficulty_instruction}
5. For each question, provide a concise but accurate answer immediately following it, derived ONLY from the context.

FORMAT EXPECTED:
Q1. [Question Text]
Answer: [Concise Answer]

Q2. [Question Text]
Answer: [Concise Answer]
...
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Topic to test: {query}\n\nContext:\n{context}")
    ])
    
    # 5. Generate Questions using Gemini
    try:
        llm = get_llm()
        chain = prompt | llm
        
        logger.info("Invoking Gemini LLM for question generation...")
        response = chain.invoke({
            "num_questions": num_questions,
            "query": query, 
            "context": context
        })
        
        logger.info("Successfully generated interview questions.")
        return response.content
        
    except Exception as e:
        logger.exception(f"Error occurred during question generation: {e}")
        raise GenerationError(f"Failed to generate questions: {e}") from e
