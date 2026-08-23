"""
SkillSwap Arena — Redis Health Monitoring (Phase 6)

Provides health checking and latency verification for Redis.
Never exposes credentials, secrets, or internal connection strings.
"""
import time
from typing import Any, Dict
from app.infrastructure.redis.client import redis_client


def check_redis_health() -> Dict[str, Any]:
    """
    Performs an active health check on Redis.
    Returns safe, non-sensitive health metadata for /health/redis.
    """
    start_time = time.perf_counter()
    is_live = redis_client.is_available()
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if is_live:
        return {
            "status": "healthy",
            "mode": "live_redis",
            "latency_ms": latency_ms,
            "connected": True,
        }
    else:
        return {
            "status": "degraded",
            "mode": "in_memory_fallback",
            "latency_ms": latency_ms,
            "connected": False,
            "message": "Operating in memory-safe fallback mode for local development/testing.",
        }
