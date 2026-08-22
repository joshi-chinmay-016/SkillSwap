import time
import logging
from fastapi import HTTPException, status, Request
from app.core.config import settings
from app.core.redis import redis_client
from app.core.logging import log_structured_event

logger = logging.getLogger("skillswap.rate_limiter")


def enforce_sliding_window_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
    action: str,
    identifier: str | int,
    error_message: str | None = None
) -> None:
    """
    Core sliding-window rate limiter using Redis sorted sets.
    Tracks timestamps as scores in sorted sets. Old timestamps are evicted automatically.
    """
    if not getattr(settings, "RATE_LIMIT_ENABLED", True):
        return

    try:
        now = time.time()
        window_start = now - window_seconds

        # Evict timestamps outside sliding window
        redis_client.zremrangebyscore(key, 0, window_start)

        # Count current timestamps in window
        current_count = redis_client.zcard(key)

        if current_count >= limit:
            log_structured_event(
                "rate_limit_triggered",
                identifier=str(identifier),
                action=action,
                current_count=current_count,
                limit=limit,
                window_seconds=window_seconds
            )
            msg = error_message or f"Too many requests for {action}. Limit is {limit} requests per {window_seconds}s. Please wait."
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=msg
            )

        # Record current request timestamp
        redis_client.zadd(key, {f"{now}-{current_count}": now})
        redis_client.expire(key, window_seconds * 2)

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Rate limiter error for {key}: {e}")
        # Fail open gracefully
        return


def enforce_booking_rate_limit(user_id: int) -> None:
    limit = getattr(settings, "BOOKING_RATE_LIMIT", 10)
    window = getattr(settings, "BOOKING_RATE_WINDOW_SECONDS", 60)
    key = f"rate_limit:booking:{user_id}"
    enforce_sliding_window_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window,
        action="booking_attempt",
        identifier=user_id,
        error_message=f"Too many booking attempts. You can only make {limit} booking requests per minute. Please wait."
    )


def enforce_auth_rate_limit(client_identifier: str) -> None:
    limit = getattr(settings, "AUTH_RATE_LIMIT", 20)
    window = getattr(settings, "AUTH_RATE_WINDOW_SECONDS", 60)
    key = f"rate_limit:auth:{client_identifier}"
    enforce_sliding_window_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window,
        action="auth_attempt",
        identifier=client_identifier,
        error_message="Too many authentication attempts. Please try again shortly."
    )


def enforce_ws_rate_limit(client_identifier: str | int) -> None:
    limit = getattr(settings, "WS_RATE_LIMIT", 30)
    window = getattr(settings, "WS_RATE_WINDOW_SECONDS", 60)
    key = f"rate_limit:ws:{client_identifier}"
    enforce_sliding_window_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window,
        action="ws_connection",
        identifier=client_identifier,
        error_message="Too many WebSocket connection attempts. Please slow down."
    )


def enforce_action_rate_limit(
    action_name: str,
    identifier: str | int,
    limit: int | None = None,
    window_seconds: int | None = None
) -> None:
    limit = limit or getattr(settings, "ACTION_RATE_LIMIT", 30)
    window_seconds = window_seconds or getattr(settings, "ACTION_RATE_WINDOW_SECONDS", 60)
    key = f"rate_limit:action:{action_name}:{identifier}"
    enforce_sliding_window_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window_seconds,
        action=action_name,
        identifier=identifier,
        error_message=f"Too many requests for {action_name}. Please wait a moment."
    )


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"
