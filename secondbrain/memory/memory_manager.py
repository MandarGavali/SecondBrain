from secondbrain.memory.long_term import LongTermMemory
from secondbrain.core.logger import get_logger
from secondbrain.core.exceptions import MemoryError

logger = get_logger("memory.manager")


class MemoryManager:

    def __init__(self):
        self.long_term = LongTermMemory()

    def get_long_term(self, user_id, query, limit=5):
        try:
            return self.long_term.search_memory(user_id=user_id, query=query, limit=limit)
        except Exception as e:
            logger.exception("Failed to get long-term memory")
            raise MemoryError(f"Long-term memory search failed: {e}") from e

    def save_long_term(self, user_id, messages, metadata=None):
        try:
            result = self.long_term.save_memory(user_id=user_id, messages=messages, metadata=metadata)
            logger.info("Memory updated")
            return result
        except Exception as e:
            logger.exception("Failed to save long-term memory")
            raise MemoryError(f"Long-term memory save failed: {e}") from e

    def format_memories(self, memories) -> str:
        items = memories.get("results", []) if isinstance(memories, dict) else (memories or [])
        if not items:
            return ""
        return "\n".join(["Known information about the user:"] + [f"- {m['memory']}" for m in items])

    def extract_and_save_memory(self, user_id: str, user_message: str, assistant_message: str):
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message},
        ]
        try:
            result = self.long_term.save_memory(user_id=user_id, messages=messages)
            logger.info("Memory updated")
            return result
        except Exception as e:
            logger.exception("Failed to extract and save memory")
            raise MemoryError(f"Memory extraction/save failed: {e}") from e


_instance = None


def get_memory_manager() -> "MemoryManager":
    """Lazy singleton (creating MemoryManager initialises Mem0 + Qdrant + Mongo)."""
    global _instance
    if _instance is None:
        _instance = MemoryManager()
    return _instance
