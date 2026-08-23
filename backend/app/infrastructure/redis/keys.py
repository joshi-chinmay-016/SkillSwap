"""
SkillSwap Arena — Centralized Redis Key Builders (Phase 6)

All Redis keys across the application are constructed here with standard namespacing,
predictable naming conventions, collision resistance, and safe invalidation patterns.
"""
from datetime import datetime, date
from typing import Any, Optional


def rate_limit_key(scope: str, identifier: str | int) -> str:
    """Builds rate limit key, e.g. rate_limit:auth:127.0.0.1 or rate_limit:booking:42"""
    return f"rate_limit:{scope}:{identifier}"


def presence_key(session_id: int, user_id: int) -> str:
    """Builds ephemeral presence key for a session participant, e.g. presence:session:10:user:5"""
    return f"presence:session:{session_id}:user:{user_id}"


def session_presence_pattern(session_id: int) -> str:
    """Pattern for all presence keys belonging to a session."""
    return f"presence:session:{session_id}:user:*"


def booking_lock_key(mentor_id: int, start_time: Any, end_time: Any) -> str:
    """
    Builds distributed lock key for mentor booking slot concurrency.
    Example: lock:mentor:5:slot:2026-08-25T10:00:00:2026-08-25T11:00:00
    """
    start_str = start_time.isoformat() if isinstance(start_time, (datetime, date)) else str(start_time)
    end_str = end_time.isoformat() if isinstance(end_time, (datetime, date)) else str(end_time)
    return f"lock:mentor:{mentor_id}:slot:{start_str}:{end_str}"


def session_lock_key(session_id: int) -> str:
    """Builds distributed lock key for session-level state transitions, e.g. lock:session:12"""
    return f"lock:session:{session_id}"


def availability_cache_key(mentor_id: int, date_str: Optional[str] = None) -> str:
    """Builds mentor availability cache key, e.g. cache:availability:mentor:5 or cache:availability:mentor:5:date:2026-08-25"""
    if date_str:
        return f"cache:availability:mentor:{mentor_id}:date:{date_str}"
    return f"cache:availability:mentor:{mentor_id}"


def availability_pattern(mentor_id: int) -> str:
    """Pattern to invalidate all availability cache entries for a mentor."""
    return f"cache:availability:mentor:{mentor_id}*"


def profile_cache_key(user_id: int) -> str:
    """Builds user profile cache key, e.g. cache:profile:user:42"""
    return f"cache:profile:user:{user_id}"


def analytics_cache_key(user_id: int, metric_type: str = "all") -> str:
    """Builds analytics cache key, e.g. cache:analytics:user:42:metric:all"""
    return f"cache:analytics:user:{user_id}:metric:{metric_type}"


def heatmap_cache_key(user_id: int, year: Optional[int] = None) -> str:
    """Builds activity heatmap cache key, e.g. cache:heatmap:user:42:year:2026"""
    if year:
        return f"cache:heatmap:user:{user_id}:year:{year}"
    return f"cache:heatmap:user:{user_id}"


def streak_cache_key(user_id: int) -> str:
    """Builds streak cache key, e.g. cache:streak:user:42"""
    return f"cache:streak:user:{user_id}"


def recommendations_cache_key(user_id: int, limit: int = 6) -> str:
    """Builds recommendations cache key, e.g. cache:recommendations:user:42:limit:6"""
    return f"cache:recommendations:user:{user_id}:limit:{limit}"


def recommendations_pattern(user_id: int) -> str:
    """Pattern to invalidate recommendations for a user."""
    return f"cache:recommendations:user:{user_id}*"


def user_data_pattern(user_id: int) -> str:
    """Pattern to match all user-scoped cache keys."""
    return f"*:user:{user_id}*"


def session_state_key(session_id: int) -> str:
    """Builds short-lived session synchronization key, e.g. session:state:10"""
    return f"session:state:{session_id}"


def idempotency_key(scope: str, token: str) -> str:
    """Builds idempotency key for deduplication, e.g. idempotency:booking:uuid"""
    return f"idempotency:{scope}:{token}"
