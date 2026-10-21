import os
from typing import List, Dict, Any

from mem0 import Memory

from secondbrain.rag.llm.gemini_llm import get_model_name


class LongTermMemory:
    """
    Wrapper around Mem0.
    Responsible only for interacting with long-term memory.
    """

    def __init__(self):

        config = {
            "llm": {
                "provider": "gemini",
                "config": {
                    "model": get_model_name(),
                    "api_key": os.getenv("GOOGLE_API_KEY"),
                    "temperature": 0.2,
                    "max_tokens": 2048,
                },
            },

            "embedder": {
                "provider": "gemini",
                "config": {
                    "model": "models/gemini-embedding-2",
                    "api_key": os.getenv("GOOGLE_API_KEY"),
                },
            },

            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "url": os.getenv("QDRANT_URL", "http://localhost:6333"),
                    "api_key": os.getenv("QDRANT_API_KEY"),
                    "collection_name": "User_Memory",
                    "embedding_model_dims": 768,
                },
            },
        }

        self.memory = Memory.from_config(config)


    def save_memory(
        self,
        user_id: str,
        messages: List[Dict[str, str]],
        metadata: Dict[str, Any] | None = None,
    ):

        return self.memory.add(
            messages=messages,
            user_id=user_id,
            metadata=metadata or {},
        )

    def search_memory(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ):

        return self.memory.search(
            query=query,
            filters={"user_id": user_id},
            limit=limit,
        )        

    def delete_memory(
        self,
        memory_id: str,
    ):

        return self.memory.delete(memory_id)

    def get_all_memories(
        self,
        user_id: str,
    ):

        return self.memory.get_all(
            filters={"user_id": user_id}
        )

    def get_memory_context(
            self,
            user_id: str,
            query: str,
            limit: int = 5,
        ) -> str:

        memories = self.search_memory(
            user_id=user_id,
            query=query,
            limit=limit,
        )

        # Mem0 returns {"results": [{"memory": "...", ...}, ...]}; the old code
        # indexed a non-existent "content" key and iterated the dict's keys.
        results = memories.get("results", []) if isinstance(memories, dict) else memories
        return "\n".join(memory["memory"] for memory in results)