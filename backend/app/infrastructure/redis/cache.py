"""
SkillSwap Arena — Reusable Redis Cache Infrastructure (Phase 6)

Provides typed JSON caching, explicit TTLs, and targeted invalidation utilities.
Ensures stale caches never cause double bookings or inaccurate coin balances.
"""
import json
import logging
from typing import Any, Optional

from app.core.config import settings
from app.infrastructure.redis.client import redis_client
from app.infrastructure.redis.keys import (
    availability_pattern,
    analytics_cache_key,
    heatmap_cache_key,
    streak_cache_key,
    recommendations_pattern,
    profile_cache_key,
    user_data_pattern,
)

logger = logging.getLogger("skillswap.cache")


def get_json(key: str) -> Optional[Any]:
    """Retrieves and deserializes JSON from Redis. Returns None on miss or parse error."""
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.debug(f"Cache get_json error for key {key}: {e}")
    return None


def set_json(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Serializes value to JSON and stores in Redis with explicit TTL."""
    try:
        ttl_seconds = ttl if ttl is not None else getattr(settings, "REDIS_CACHE_DEFAULT_TTL", 300)
        serialized = json.dumps(value, default=str)
        return redis_client.setex(key, ttl_seconds, serialized)
    except Exception as e:
        logger.debug(f"Cache set_json error for key {key}: {e}")
        return False


def delete_keys(*keys: str) -> int:
    """Deletes one or more cache keys."""
    try:
        return redis_client.delete(*keys)
    except Exception as e:
        logger.debug(f"Cache delete error: {e}")
        return 0


def delete_pattern(pattern: str) -> int:
    """Deletes all keys matching the glob pattern."""
    try:
        return redis_client.delete_pattern(pattern)
    except Exception as e:
        logger.debug(f"Cache delete_pattern error for {pattern}: {e}")
        return 0


# --- Targeted Invalidation Strategies ---

def invalidate_mentor_availability(mentor_id: int) -> int:
    """Invalidates all cached availability windows for a mentor upon schedule edit or booking."""
    return delete_pattern(availability_pattern(mentor_id))


def invalidate_user_learning_data(user_id: int) -> int:
    """Invalidates streak, heatmap, and learning analytics caches for a user."""
    count = 0
    count += delete_pattern(f"cache:heatmap:user:{user_id}*")
    count += delete_pattern(f"cache:streak:user:{user_id}*")
    count += delete_pattern(f"cache:analytics:user:{user_id}*")
    count += delete_pattern(f"heatmap:user:{user_id}:*")
    count += delete_pattern(f"streak:user:{user_id}*")
    count += delete_pattern(f"analytics:user:{user_id}:*")
    return count


def invalidate_recommendations(user_id: int) -> int:
    """Invalidates cached recommendations when a user's skills or completed sessions change."""
    count = delete_pattern(recommendations_pattern(user_id))
    count += delete_pattern(f"recommendations:*:user:{user_id}:*")
    return count


def invalidate_user_profile(user_id: int) -> int:
    """Invalidates user profile and discovery caches."""
    return delete_keys(profile_cache_key(user_id))
