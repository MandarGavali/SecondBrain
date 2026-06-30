from secondbrain.utils.logger import logger
import os
import time
import re
from pathlib import Path
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from langchain_google_genai import ChatGoogleGenerativeAI
from secondbrain.core.logger import get_logger
from secondbrain.core.exceptions import GeminiError

logger = get_logger("rag.llm")

def execute_with_retry(api_func, *args, max_attempts=5, **kwargs):
    """
    Executes a Gemini API function with automatic retry on 429/RESOURCE_EXHAUSTED errors.
    Uses retryDelay from the error details if available, otherwise uses exponential backoff.
    
    This is added to resolve the 429 RESOURCE_EXHAUSTED errors under the Gemini free tier limit.
    """
    attempt = 0
    backoff = 2.0
    
    while True:
        try:
            return api_func(*args, **kwargs)
        except ClientError as e:
            attempt += 1
            # Check if this is a 429 RESOURCE_EXHAUSTED rate limit
            is_429 = (e.code == 429) or ("quota" in str(e).lower()) or ("exhausted" in str(e).lower())
            
            if not is_429 or attempt >= max_attempts:
                # If it's not a 429, or we've exceeded max attempts, raise
                logger.exception(f"Gemini API request failed: {e}")
                raise GeminiError(f"Gemini API request failed: {e}") from e
            
            # Determine sleep time
            sleep_time = None
            details = getattr(e, "details", None)
            if isinstance(details, dict):
                error_dict = details.get("error", {})
                inner_details = error_dict.get("details", [])
                for detail in inner_details:
                    if isinstance(detail, dict) and "retryDelay" in detail:
                        delay_str = detail["retryDelay"]
                        # Extract the numeric part of the delay (e.g. "54s" or "54.12s" -> 54.12)
                        match = re.search(r"([\d\.]+)", delay_str)
                        if match:
                            sleep_time = float(match.group(1)) + 1.0  # Add 1s safety margin
                            break
            
            if sleep_time is None:
                sleep_time = backoff
                backoff *= 2.0
                
            logger.warning(f"\n[RATE LIMIT] Gemini 429 rate limit hit. Sleeping for {sleep_time:.2f} seconds before retry {attempt}/{max_attempts}...")
            time.sleep(sleep_time)
        except Exception as e:
            logger.exception(f"Unexpected error during Gemini API request: {e}")
            raise GeminiError(f"Unexpected error: {e}") from e

def get_llm() -> ChatGoogleGenerativeAI:

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found. Check your .env file.")
    # Set max_retries=10 to handle rate limits in LangChain calls
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        max_retries=10
    )

def generate_answer(query: str, context: str) -> str:
    """Generates an answer using the Gemini LLM based on provided context."""
    
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found. Check your .env file.")

    client = genai.Client(api_key=google_api_key)

    system_prompt = f"""
You are SecondBrain, a trusted knowledge retrieval assistant.

MISSION:
Provide accurate, grounded answers strictly from the supplied context.

INSTRUCTIONS:

1. Use ONLY the provided context.
2. Never hallucinate.
3. Never make assumptions.
4. If evidence is insufficient, say so explicitly.
5. Merge information from multiple sections when needed.
6. Prefer precise answers over broad speculation.
7. Cite relevant page numbers.
8. Guide users to the most useful pages for deeper reading.

OUTPUT FORMAT:

Answer:
<answer>

Evidence Summary:
<short explanation of where the answer came from>

Source Pages:
<page numbers>

Confidence:
High / Medium / Low

Context:
{context}
"""

    # Wrap SDK call with execute_with_retry helper to survive 429 rate limits
    logger.info("Sending request to Gemini")
    response = execute_with_retry(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=query,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt
        )
    )
    logger.info("Gemini response received")
    return response.text

def generate_chat_response(query: str, history: list = None) -> str:
    """Generates a chat response using the Gemini LLM without RAG context.
    
    FIX: The `history` parameter accepts a list of prior LangChain messages
    (HumanMessage / AIMessage) restored from the MongoDB checkpoint.
    These are formatted into a conversation prefix and prepended to the prompt
    so the LLM is aware of the conversation context from previous turns.
    """
    
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found. Check your .env file.")

    client = genai.Client(api_key=google_api_key)

    system_prompt = "You are a helpful AI assistant. Answer the user's questions clearly and concisely."

    # FIX: Build conversation history prefix from restored checkpoint messages.
    # If history is empty or None, this is a no-op and behaves exactly as before.
    history_prefix = ""
    if history:
        history_lines = []
        for msg in history:
            # Determine role label based on message class name (avoids importing types here)
            role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
            history_lines.append(f"{role}: {msg.content}")
        history_prefix = "\n".join(history_lines) + "\n\n"

    full_prompt = f"{history_prefix}User: {query}"

    # Wrap SDK call with execute_with_retry helper to survive 429 rate limits
    logger.info("Sending request to Gemini")
    response = execute_with_retry(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt
        )
    )
    logger.info("Gemini response received")
    return response.text

