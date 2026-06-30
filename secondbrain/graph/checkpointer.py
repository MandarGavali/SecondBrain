from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

import os

DB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

# Global client and saver so we don't recreate them constantly
_mongo_client = None
_saver = None

def get_checkpointer():
    """
    Returns a MongoDB checkpointer for LangGraph.
    """
    global _mongo_client, _saver
    if _saver is None:
        _mongo_client = MongoClient(DB_URI)
        _saver = MongoDBSaver(_mongo_client)
    return _saver