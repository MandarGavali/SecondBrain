from secondbrain.utils.logger import logger
import os
from pathlib import Path
from google import genai
from google.genai import types
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY: 
  raise ValueError("GOOGLE_API_KEY not found. Check your .env file")

#Initialize Gemini client 
client = genai.Client(api_key=GOOGLE_API_KEY)

#3. Embedding model 

embedding_model = GoogleGenerativeAIEmbeddings(
  model="models/gemini-embedding-2",
  google_api_key = GOOGLE_API_KEY
)
# logger.info("Embedding model ready [OK]")

vector_db = QdrantVectorStore.from_existing_collection(
  url=os.getenv("QDRANT_URL", "http://localhost:6333"),
  collection_name="Learning_RAG",
  embedding=embedding_model
)

user_query = input("ask something: ")

search_results = vector_db.similarity_search(query=user_query, k=10 )

context = "\n\n\n".join(
    [
        f"Page Content: {result.page_content}\n"
        f"Page Number: {result.metadata['page_label']}\n"
        f"File Location: {result.metadata['source']}"
        for result in search_results
    ]
)

SYSTEM_PROMPT = f"""
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

#generating response

response = client.models.generate_content(
  model = "gemini-2.5-flash",
  contents= user_query,
  config=types.GenerateContentConfig(
    system_instruction = SYSTEM_PROMPT
  )
)

logger.info(f"AI🤖 : {response.text}")