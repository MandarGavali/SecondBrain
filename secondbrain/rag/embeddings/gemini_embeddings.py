from secondbrain.utils.logger import logger
import os
from pathlib import Path
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    """Creates and returns the Gemini embedding model."""
    
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found. Check your .env file.")

    embedding_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=google_api_key
    )
    # logger.info("Embedding model ready [OK]")
    return embedding_model
