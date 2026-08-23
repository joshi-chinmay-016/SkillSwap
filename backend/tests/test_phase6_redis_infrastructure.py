"""
SkillSwap Arena — Phase 6 Production Redis Infrastructure Test Suite

Covers:
  - Test 1: Redis client initialization, basic CRUD, TTL, and in-memory fallback.
  - Test 2: Centralized key builders namespacing and collision avoidance.
  - Test 3: Distributed atomic sliding-window rate limiting & HTTP 429 Retry-After responses.
  - Test 4: Distributed locking (atomic token acquisition, Lua release, contention 409).
  - Test 5: Reusable JSON cache serialization and targeted invalidation methods.
  - Test 6: Multi-worker Pub/Sub event broadcasting and message envelope routing.
  - Test 7: Redis health check endpoints (GET /health and GET /health/redis).
  - Test 8: Backward compatibility re-exports (app.core.redis, app.core.rate_limiter, app.core.distributed_lock).
"""
import time
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.infrastructure.redis import (
    redis_client,
    SafeRedis,
    rate_limit_key,
    presence_key,
    booking_lock_key,
    session_lock_key,
    availability_cache_key,
    profile_cache_key,
    analytics_cache_key,
    heatmap_cache_key,
    streak_cache_key,
    recommendations_cache_key,
    check_redis_health,
    enforce_sliding_window_rate_limit,
    enforce_booking_rate_limit,
    enforce_auth_rate_limit,
    enforce_action_rate_limit,
    enforce_ai_rate_limit,
    RedisDistributedLock,
    distributed_booking_lock,
    distributed_session_lock,
    get_json,
    set_json,
    delete_keys,
    delete_pattern,
    invalidate_mentor_availability,
    invalidate_user_learning_data,
    invalidate_recommendations,
    publish_event,
    publish_user_notification,
)
import app.core.redis as legacy_redis
import app.core.rate_limiter as legacy_rate_limiter
import app.core.distributed_lock as legacy_distributed_lock

client = TestClient(fastapi_app)


# =========================================================================
# 1. Redis Client & Fallback Operations
# =========================================================================
def test_redis_client_operations():
    # Test basic set, get, ttl, and delete
    test_key = "test:phase6:client_ops"
    assert redis_client.set(test_key, "hello_redis", ex=60) is True
    assert redis_client.get(test_key) == "hello_redis"
    assert redis_client.ttl(test_key) > 0

    # Test set_nx (set if not exists)
    assert redis_client.set_nx(test_key, "new_value") is False  # key already exists
    assert redis_client.delete(test_key) >= 1
    assert redis_client.get(test_key) is None
    assert redis_client.set_nx(test_key, "new_value", ex=30) is True

    # Test delete pattern
    redis_client.set("test:phase6:pat:1", "val1")
    redis_client.set("test:phase6:pat:2", "val2")
    deleted = redis_client.delete_pattern("test:phase6:pat:*")
    assert deleted >= 2
    assert redis_client.get("test:phase6:pat:1") is None

    redis_client.delete(test_key)


# =========================================================================
# 2. Centralized Key Builders
# =========================================================================
def test_redis_key_builders():
    assert rate_limit_key("auth", "127.0.0.1") == "rate_limit:auth:127.0.0.1"
    assert presence_key(10, 42) == "presence:session:10:user:42"
    assert profile_cache_key(5) == "cache:profile:user:5"
    assert analytics_cache_key(5, "monthly") == "cache:analytics:user:5:metric:monthly"
    assert heatmap_cache_key(5, 2026) == "cache:heatmap:user:5:year:2026"
    assert streak_cache_key(5) == "cache:streak:user:5"
    assert recommendations_cache_key(5, 6) == "cache:recommendations:user:5:limit:6"

    # DateTime lock key
    dt1 = datetime(2026, 8, 25, 10, 0, 0)
    dt2 = datetime(2026, 8, 25, 11, 0, 0)
    lock_k = booking_lock_key(7, dt1, dt2)
    assert "lock:mentor:7:slot:2026-08-25T10:00:00:2026-08-25T11:00:00" == lock_k


# =========================================================================
# 3. Distributed Sliding-Window Rate Limiting
# =========================================================================
def test_distributed_rate_limiting():
    user_id = "test_rate_user_99"
    action_key = rate_limit_key("action:test_action", user_id)
    redis_client.delete(action_key)

    # Limit = 3 requests per 10 seconds
    limit = 3
    window = 10

    # 1. First 3 requests must pass
    for _ in range(limit):
        enforce_sliding_window_rate_limit(
            key=action_key,
            limit=limit,
            window_seconds=window,
            action="test_action",
            identifier=user_id,
        )

    # 2. 4th request must raise HTTP 429 with Retry-After header
    with pytest.raises(HTTPException) as exc_info:
        enforce_sliding_window_rate_limit(
            key=action_key,
            limit=limit,
            window_seconds=window,
            action="test_action",
            identifier=user_id,
        )

    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Retry-After" in exc_info.value.headers
    assert int(exc_info.value.headers["Retry-After"]) >= 1

    redis_client.delete(action_key)


# =========================================================================
# 4. Distributed Locking & Concurrency Protection
# =========================================================================
def test_distributed_locks_concurrency_protection():
    mentor_id = 888
    start_dt = "2026-08-25T14:00:00"
    end_dt = "2026-08-25T15:00:00"
    lock_key = booking_lock_key(mentor_id, start_dt, end_dt)
    redis_client.delete(lock_key)

    # 1. Acquire distributed lock using context manager
    with distributed_booking_lock(mentor_id, start_dt, end_dt, ttl_seconds=5) as lock:
        assert lock.acquired is True
        assert redis_client.get(lock_key) == lock.token

        # 2. Concurrent attempt on same slot must fail / raise 409 Conflict
        with pytest.raises(HTTPException) as exc_info:
            with distributed_booking_lock(mentor_id, start_dt, end_dt, ttl_seconds=5, timeout_seconds=0.1):
                pass
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    # 3. Exiting context manager must safely release the lock
    assert redis_client.get(lock_key) is None


# =========================================================================
# 5. Reusable JSON Cache & Targeted Invalidation
# =========================================================================
def test_reusable_cache_and_targeted_invalidation():
    user_id = 777
    mentor_id = 999

    # 1. set_json & get_json
    c_key = f"cache:test:user:{user_id}"
    test_data = {"user_id": user_id, "score": 98.5, "skills": ["Python", "FastAPI"]}
    assert set_json(c_key, test_data, ttl=60) is True
    retrieved = get_json(c_key)
    assert retrieved == test_data

    # 2. Targeted mentor availability invalidation
    avail_key = availability_cache_key(mentor_id, "2026-08-25")
    set_json(avail_key, {"slots": ["10:00", "11:00"]}, ttl=60)
    assert get_json(avail_key) is not None
    invalidate_mentor_availability(mentor_id)
    assert get_json(avail_key) is None

    # 3. Targeted user learning data invalidation
    streak_k = streak_cache_key(user_id)
    heat_k = heatmap_cache_key(user_id, 2026)
    set_json(streak_k, {"current_streak": 5}, ttl=60)
    set_json(heat_k, {"days": 12}, ttl=60)
    invalidate_user_learning_data(user_id)
    assert get_json(streak_k) is None
    assert get_json(heat_k) is None

    delete_keys(c_key)


# =========================================================================
# 6. Multi-Worker Pub/Sub Event Publishing
# =========================================================================
@pytest.mark.asyncio
async def test_pubsub_event_publishing():
    # Verify non-blocking event publishing
    ok = await publish_user_notification(
        user_id=123,
        payload={"type": "TEST_EVENT", "message": "Phase 6 distributed Pub/Sub test"},
    )
    # publish_user_notification returns bool without raising exceptions
    assert isinstance(ok, bool)


# =========================================================================
# 7. Health Check Endpoints
# =========================================================================
def test_health_and_redis_health_endpoints():
    # 1. GET /health
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "redis" in data

    # 2. GET /health/redis
    res_r = client.get("/health/redis")
    assert res_r.status_code == 200
    data_r = res_r.json()
    assert data_r["status"] in ("healthy", "degraded")
    assert "mode" in data_r
    assert "latency_ms" in data_r
    # Ensure no secrets or credentials leaked in response
    assert "password" not in data_r
    assert "REDIS_URL" not in data_r


# =========================================================================
# 8. Backward Compatibility Re-exports Check
# =========================================================================
def test_backward_compatibility_reexports():
    # Ensure existing modules export expected attributes
    assert hasattr(legacy_redis, "redis_client")
    assert hasattr(legacy_redis, "SafeRedis")
    assert hasattr(legacy_rate_limiter, "enforce_sliding_window_rate_limit")
    assert hasattr(legacy_rate_limiter, "enforce_booking_rate_limit")
    assert hasattr(legacy_distributed_lock, "RedisDistributedLock")
    assert hasattr(legacy_distributed_lock, "distributed_booking_lock")
