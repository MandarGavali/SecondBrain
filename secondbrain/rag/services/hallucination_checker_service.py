import os
from pathlib import Path
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI



# Initialize LangChain Gemini model (similar to other grading/rewriting services)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    max_retries=10
)

def check_hallucination(answer: str, documents: list[Document]) -> tuple[bool, str]:
    """
    Checks if the generated answer is grounded in the provided documents.
    Returns a tuple of (is_grounded: bool, verification_reason: str).
    """
    context = "\n\n".join([doc.page_content for doc in documents])
    
    prompt = f"""
You are a hallucination grader.
Given the following context and answer, verify if the answer is completely grounded in the context.

Context:
{context}

Answer:
{answer}

Respond ONLY with YES or NO on the first line, followed by a brief reason on the second line.
"""
    
    response = llm.invoke(prompt)
    content_lines = response.content.strip().split("\n")
    
    # FIX: Use startswith instead of exact equality.
    # Gemini sometimes responds with 'YES.' or 'YES,' which broke strict == 'YES' checks.
    first_line = content_lines[0].strip().upper().rstrip(".,!- ")
    is_grounded = first_line.startswith("YES")
    reason = content_lines[1].strip() if len(content_lines) > 1 else "No reason provided."
    
    return is_grounded, reason
