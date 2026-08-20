import time
import logging
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.redis import redis_client
from app.core.logging import log_structured_event

logger = logging.getLogger("skillswap.rate_limiter")


def enforce_booking_rate_limit(user_id: int) -> None:
    """
    Enforces sliding-window rate limiting on booking actions using Redis.
    Limits each user to BOOKING_RATE_LIMIT requests per BOOKING_RATE_WINDOW_SECONDS.

    Graceful degradation:
    If Redis is unavailable, logs a warning and fails open to let PostgreSQL
    handle authoritative transaction safety.
    """
    limit = getattr(settings, "BOOKING_RATE_LIMIT", 10)
    window = getattr(settings, "BOOKING_RATE_WINDOW_SECONDS", 60)
    key = f"rate_limit:booking:{user_id}"

    try:
        now = time.time()
        window_start = now - window

        # Clean old records outside the sliding window
        redis_client.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        current_count = redis_client.zcard(key)

        if current_count >= limit:
            log_structured_event(
                "rate_limit_triggered",
                user_id=user_id,
                action="booking_attempt",
                current_count=current_count,
                limit=limit,
                window_seconds=window
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many booking attempts. You can only make {limit} booking requests per minute. Please wait."
            )

        # Add current timestamp to sorted set
        redis_client.zadd(key, {str(now): now})
        redis_client.expire(key, window * 2)

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Redis rate limiter bypassed due to error: {e}")
        # Fail-open gracefully
        return
