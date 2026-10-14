import json
from typing import Any

from secondbrain.core.logger import get_logger

logger = get_logger("lomcp.cache")

_local: dict[str, str] = {}
_redis_client = None
_redis_checked = False


def _get_redis():
    """Return a working Redis connection or None (then an in-process dict is used)."""
    global _redis_client, _redis_checked
    if not _redis_checked:
        _redis_checked = True
        try:
            from secondbrain.queues.client import redis_connection

            redis_connection.ping()
            _redis_client = redis_connection
        except Exception as e:
            logger.warning(f"Redis unavailable for LO-MCP cache, using in-process cache: {e}")
    return _redis_client


def get_json(key: str) -> Any | None:
    client = _get_redis()
    try:
        raw = client.get(key) if client else _local.get(key)
    except Exception:
        raw = _local.get(key)
    return json.loads(raw) if raw else None


def set_json(key: str, value: Any) -> None:
    payload = json.dumps(value)
    client = _get_redis()
    _local[key] = payload
    if client:
        try:
            client.set(key, payload)
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")
