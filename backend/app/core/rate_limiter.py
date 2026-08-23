"""
SkillSwap Arena — Rate Limiter Core Interface (Phase 6 Forwarding Layer)

Re-exports distributed rate limiting utilities from app.infrastructure.redis.rate_limiter
for backward compatibility across all existing endpoints and tests.
"""
from app.infrastructure.redis.rate_limiter import (
    enforce_sliding_window_rate_limit,
    enforce_booking_rate_limit,
    enforce_auth_rate_limit,
    enforce_ws_rate_limit,
    enforce_action_rate_limit,
    enforce_ai_rate_limit,
    get_client_ip,
)

__all__ = [
    "enforce_sliding_window_rate_limit",
    "enforce_booking_rate_limit",
    "enforce_auth_rate_limit",
    "enforce_ws_rate_limit",
    "enforce_action_rate_limit",
    "enforce_ai_rate_limit",
    "get_client_ip",
]
