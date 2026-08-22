import json
import logging
from typing import Any, Tuple
from app.core.config import settings
from app.core.redis import redis_client
from app.core.logging import log_structured_event

logger = logging.getLogger("skillswap.idempotency")


def get_idempotency_key(user_id: int | str, key: str) -> str:
    return f"idempotency:{user_id}:{key}"


def get_idempotent_response(user_id: int | str, key: str | None) -> Tuple[int, Any] | None:
    """
    Checks if an idempotent response has already been cached for this user and idempotency key.
    Returns (status_code, data_dict) or None.
    """
    if not key or not getattr(settings, "IDEMPOTENCY_ENABLED", True):
        return None

    redis_key = get_idempotency_key(user_id, key)
    cached_val = redis_client.get(redis_key)
    if not cached_val:
        return None

    try:
        record = json.loads(cached_val)
        log_structured_event(
            "idempotency_cache_hit",
            user_id=user_id,
            idempotency_key=key
        )
        return record.get("status_code", 200), record.get("data")
    except Exception as e:
        logger.warning(f"Failed to decode idempotency record for {redis_key}: {e}")
        return None


def save_idempotent_response(
    user_id: int | str,
    key: str | None,
    status_code: int,
    data: Any
) -> None:
    """
    Caches the completed mutation response in Redis for IDEMPOTENCY_TTL_SECONDS.
    """
    if not key or not getattr(settings, "IDEMPOTENCY_ENABLED", True):
        return

    redis_key = get_idempotency_key(user_id, key)
    ttl = getattr(settings, "IDEMPOTENCY_TTL_SECONDS", 300)

    try:
        # If data is a Pydantic model or SQLAlchemy object, convert appropriately
        if hasattr(data, "model_dump"):
            serializable_data = data.model_dump(mode="json")
        elif hasattr(data, "dict"):
            serializable_data = data.dict()
        elif isinstance(data, dict):
            serializable_data = data
        else:
            # Fallback representation
            serializable_data = str(data)

        payload = json.dumps({
            "status_code": status_code,
            "data": serializable_data
        })
        redis_client.setex(redis_key, ttl, payload)
        log_structured_event(
            "idempotency_saved",
            user_id=user_id,
            idempotency_key=key,
            ttl=ttl
        )
    except Exception as e:
        logger.warning(f"Failed to store idempotency record for {redis_key}: {e}")
