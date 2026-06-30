from secondbrain.memory.short_term import ShortTermMemory
from secondbrain.memory.long_term import LongTermMemory
from secondbrain.core.logger import get_logger
from secondbrain.core.exceptions import MemoryError

logger = get_logger("memory.manager")


class MemoryManager:

    def __init__(self):

        self.short_term = ShortTermMemory()

        self.long_term = LongTermMemory()

    def get_short_term(self, thread_id):
        try:
            return self.short_term.get_messages(thread_id)
        except Exception as e:
            logger.exception("Failed to get short-term memory")
            raise MemoryError(f"Short-term memory failed: {e}") from e

    def get_long_term(self, user_id, query, limit=5):
        logger.info("Memory loading")
        try:
            results = self.long_term.search_memory(
                user_id=user_id,
                query=query,
                limit=limit,
            )
            logger.info("Memory loaded")
            return results
        except Exception as e:
            logger.exception("Failed to get long-term memory")
            raise MemoryError(f"Long-term memory search failed: {e}") from e

    def get_context(
        self,
        thread_id,
        user_id,
        query,
    ):

        return {
            "conversation": self.get_short_term(thread_id),
            "memories": self.get_long_term(user_id, query),
        }

    def save_long_term(
        self,
        user_id,
        messages,
        metadata=None,
    ):
        try:
            result = self.long_term.save_memory(
                user_id=user_id,
                messages=messages,
                metadata=metadata,
            )
            logger.info("Memory updated")
            return result
        except Exception as e:
            logger.exception("Failed to save long-term memory")
            raise MemoryError(f"Long-term memory save failed: {e}") from e

    def format_memories(self, memories):

        if not memories:
            return ""

        lines = [
            "Known information about the user:"
        ]

        for memory in memories["results"]:
            lines.append(
                f"- {memory['memory']}"
            )

        return "\n".join(lines)

    def extract_and_save_memory(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str,
    ):
        messages = [
            {
                "role": "user",
                "content": user_message,
            },
            {
                "role": "assistant",
                "content": assistant_message,
            },
        ]

        try:
            result = self.long_term.save_memory(
                user_id=user_id,
                messages=messages,
            )
            logger.info("Memory updated")
            return result
        except Exception as e:
            logger.exception("Failed to extract and save memory")
            raise MemoryError(f"Memory extraction/save failed: {e}") from e