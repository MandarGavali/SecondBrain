import os
from datetime import datetime, timezone

from secondbrain.core.logger import get_logger

logger = get_logger("memory.status_store")


class MemoryStatusStore:
    """Audit table: which Mem0 memories are deprecated, and why (MongoDB)."""

    def __init__(self, uri: str | None = None, db: str = "secondbrain", collection: str = "memory_status"):
        self._uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self._db_name = db
        self._coll_name = collection
        self._coll = None

    def _collection(self):
        if self._coll is None:
            from pymongo import MongoClient

            self._coll = MongoClient(self._uri)[self._db_name][self._coll_name]
            self._coll.create_index("memory_id", unique=True)
            self._coll.create_index([("user_id", 1), ("status", 1)])
        return self._coll

    def deprecated_ids(self, user_id: str) -> set[str]:
        try:
            cur = self._collection().find({"user_id": user_id, "status": "deprecated"}, {"memory_id": 1})
            return {d["memory_id"] for d in cur}
        except Exception as e:
            logger.warning(f"deprecated_ids failed, treating all memories as active: {e}")
            return set()

    def deprecate(self, memory_id: str, user_id: str, old_text: str | None,
                  superseded_by: str | None, new_text: str, reason: str) -> None:
        self._collection().update_one(
            {"memory_id": memory_id},
            {"$set": {
                "memory_id": memory_id,
                "user_id": user_id,
                "status": "deprecated",
                "old_text": old_text,
                "superseded_by": superseded_by,
                "new_text": new_text,
                "reason": reason,
                "deprecated_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )

    def history(self, user_id: str) -> list[dict]:
        return list(self._collection().find({"user_id": user_id}, {"_id": 0}))


_store: MemoryStatusStore | None = None


def get_status_store() -> MemoryStatusStore:
    global _store
    if _store is None:
        _store = MemoryStatusStore()
    return _store
