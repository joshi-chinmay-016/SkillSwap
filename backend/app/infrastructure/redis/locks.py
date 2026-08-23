"""
SkillSwap Arena — Distributed Coordination Locks (Phase 6)

Provides atomic Redis locks with token ownership and safe TTL expiration.
Guarantees that race conditions during concurrent bookings or session state transitions
are prevented across multiple worker instances.
"""
import time
import uuid
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator, Optional
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logging import log_structured_event
from app.infrastructure.redis.client import redis_client
from app.infrastructure.redis.keys import booking_lock_key, session_lock_key

logger = logging.getLogger("skillswap.lock")

# Atomic Lua script ensuring only the lock owner (matching token) can delete the key
LUA_RELEASE_LOCK = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class RedisDistributedLock:
    """
    Coordination lock using Redis with unique token ownership and safe TTL.
    Prevents double booking and concurrent state mutation.
    """

    def __init__(
        self,
        lock_key: str,
        ttl_seconds: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
        retry_delay_seconds: float = 0.05,
    ):
        self.lock_key = lock_key
        self.ttl_seconds = ttl_seconds or getattr(settings, "DISTRIBUTED_LOCK_TTL_SECONDS", 10)
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else getattr(settings, "DISTRIBUTED_LOCK_TIMEOUT_SECONDS", 2.0)
        )
        self.retry_delay_seconds = retry_delay_seconds
        self.token = str(uuid.uuid4())
        self.acquired = False

    def acquire(self) -> bool:
        if not getattr(settings, "DISTRIBUTED_LOCK_ENABLED", True):
            return True

        start_time = time.time()
        while True:
            # Atomic set NX with TTL
            ok = redis_client.set_nx(self.lock_key, self.token, ex=self.ttl_seconds)
            if ok:
                self.acquired = True
                log_structured_event(
                    "lock_acquired",
                    lock_key=self.lock_key,
                    token=self.token,
                    ttl=self.ttl_seconds,
                )
                return True

            if (time.time() - start_time) >= self.timeout_seconds:
                log_structured_event(
                    "lock_timeout",
                    lock_key=self.lock_key,
                    timeout=self.timeout_seconds,
                )
                return False

            time.sleep(self.retry_delay_seconds)

    def release(self) -> bool:
        if not self.acquired:
            return True

        try:
            res = redis_client.eval_lua(LUA_RELEASE_LOCK, 1, self.lock_key, self.token)
            log_structured_event(
                "lock_released",
                lock_key=self.lock_key,
                success=bool(res),
            )
            return bool(res)
        except Exception as e:
            logger.warning(f"Error releasing Redis distributed lock {self.lock_key}: {e}")
            return False
        finally:
            self.acquired = False


@contextmanager
def distributed_booking_lock(
    mentor_id: int,
    start_time: Any,
    end_time: Any,
    ttl_seconds: Optional[int] = None,
    timeout_seconds: Optional[float] = None,
) -> Generator[RedisDistributedLock, None, None]:
    """
    Context manager for distributed booking lock around mentor slots.
    Raises HTTP 409 Conflict if lock cannot be acquired within timeout.
    """
    lock_key = booking_lock_key(mentor_id, start_time, end_time)
    lock = RedisDistributedLock(
        lock_key=lock_key,
        ttl_seconds=ttl_seconds,
        timeout_seconds=timeout_seconds,
    )

    acquired = lock.acquire()
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot is currently being reserved by another learner. Please choose another time.",
        )

    try:
        yield lock
    finally:
        lock.release()


@contextmanager
def distributed_session_lock(
    session_id: int,
    ttl_seconds: Optional[int] = None,
    timeout_seconds: Optional[float] = None,
) -> Generator[RedisDistributedLock, None, None]:
    """
    Context manager for session state transitions (start/complete/cancel).
    """
    lock_key = session_lock_key(session_id)
    lock = RedisDistributedLock(
        lock_key=lock_key,
        ttl_seconds=ttl_seconds or 5,
        timeout_seconds=timeout_seconds or 1.5,
    )

    acquired = lock.acquire()
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session operation in progress. Please retry.",
        )

    try:
        yield lock
    finally:
        lock.release()
