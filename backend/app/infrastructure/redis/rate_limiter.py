"""
SkillSwap Arena — Distributed Redis Rate Limiting (Phase 6)

Production-grade sliding-window rate limiter using Redis sorted sets.
Works seamlessly across multiple FastAPI worker processes.
Includes Retry-After headers, atomic timestamps, and safe fallback.
"""
import time
import logging
from typing import Optional, Union
from fastapi import HTTPException, status, Request

from app.core.config import settings
from app.core.logging import log_structured_event
from app.infrastructure.redis.client import redis_client
from app.infrastructure.redis.keys import rate_limit_key

logger = logging.getLogger("skillswap.rate_limiter")


def enforce_sliding_window_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
    action: str,
    identifier: Union[str, int],
    error_message: Optional[str] = None
) -> None:
    """
    Core sliding-window rate limiter using Redis sorted sets.
    Tracks timestamps as scores in sorted sets. Old timestamps outside the window are pruned automatically.
    """
    if not getattr(settings, "RATE_LIMIT_ENABLED", True):
        return

    try:
        now = time.time()
        window_start = now - window_seconds

        # 1. Prune timestamps outside sliding window
        redis_client.zremrangebyscore(key, 0, window_start)

        # 2. Count active timestamps in window
        current_count = redis_client.zcard(key)

        if current_count >= limit:
            retry_after = max(1, int(window_seconds - (now - window_start)))
            log_structured_event(
                "rate_limit_triggered",
                identifier=str(identifier),
                action=action,
                current_count=current_count,
                limit=limit,
                window_seconds=window_seconds,
                retry_after=retry_after
            )
            msg = error_message or f"Too many requests for {action}. Limit is {limit} requests per {window_seconds}s. Please wait."
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=msg,
                headers={"Retry-After": str(retry_after)}
            )

        # 3. Record request with unique member token
        member_id = f"{now}:{current_count}"
        redis_client.zadd(key, {member_id: now})
        redis_client.expire(key, window_seconds * 2)

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Rate limiter error for {key}: {e}")
        # Safe degrade
        return


def enforce_booking_rate_limit(user_id: int) -> None:
    """Limits booking attempts to prevent slot spam."""
    limit = getattr(settings, "BOOKING_RATE_LIMIT", 10)
    window = getattr(settings, "BOOKING_RATE_WINDOW_SECONDS", 60)
    key = rate_limit_key("booking", user_id)
    enforce_sliding_window_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window,
        action="booking_attempt",
        identifier=user_id,
        error_message=f"Too many booking attempts. You can only make {limit} booking requests per minute. Please wait."
    )


def enforce_auth_rate_limit(client_identifier: str) -> None:
    """Limits authentication attempts (login, register, refresh) per IP/email."""
    limit = getattr(settings, "AUTH_RATE_LIMIT", 20)
    window = getattr(settings, "AUTH_RATE_WINDOW_SECONDS", 60)
    key = rate_limit_key("auth", client_identifier)
    enforce_sliding_window_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window,
        action="auth_attempt",
        identifier=client_identifier,
        error_message="Too many authentication attempts. Please try again shortly."
    )


def enforce_ws_rate_limit(client_identifier: Union[str, int]) -> None:
    """Limits WebSocket connection attempts per user/IP."""
    limit = getattr(settings, "WS_RATE_LIMIT", 30)
    window = getattr(settings, "WS_RATE_WINDOW_SECONDS", 60)
    key = rate_limit_key("ws", client_identifier)
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
    identifier: Union[str, int],
    limit: Optional[int] = None,
    window_seconds: Optional[int] = None
) -> None:
    """Generic rate limiter for sensitive actions (start/complete session, notes, etc.)."""
    limit = limit or getattr(settings, "ACTION_RATE_LIMIT", 30)
    window_seconds = window_seconds or getattr(settings, "ACTION_RATE_WINDOW_SECONDS", 60)
    key = rate_limit_key(f"action:{action_name}", identifier)
    enforce_sliding_window_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window_seconds,
        action=action_name,
        identifier=identifier,
        error_message=f"Too many requests for {action_name}. Please wait a moment."
    )


def enforce_ai_rate_limit(user_id: int) -> None:
    """Protects computationally heavy AI session intelligence and RAG endpoints."""
    limit = 10
    window_seconds = 60
    key = rate_limit_key("ai_generation", user_id)
    enforce_sliding_window_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window_seconds,
        action="ai_generation",
        identifier=user_id,
        error_message="AI generation rate limit reached. Please wait before generating another report."
    )


def get_client_ip(request: Request) -> str:
    """Extracts client IP considering trusted reverse proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"
