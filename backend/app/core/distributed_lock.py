import time
import uuid
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Generator
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.redis import redis_client
from app.core.logging import log_structured_event

logger = logging.getLogger("skillswap.lock")

# Atomic Lua script ensuring only the lock owner (matching token) can release the lock
LUA_RELEASE_LOCK = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


def generate_slot_lock_key(mentor_id: int, start_time: datetime | str, end_time: datetime | str) -> str:
    """
    Standardizes lock keys across mentor booking operations.
    Example: lock:mentor:5:slot:2026-08-25T10:00:00:2026-08-25T11:00:00
    """
    start_str = start_time.isoformat() if isinstance(start_time, datetime) else str(start_time)
    end_str = end_time.isoformat() if isinstance(end_time, datetime) else str(end_time)
    return f"lock:mentor:{mentor_id}:slot:{start_str}:{end_str}"


class RedisDistributedLock:
    """
    Coordination lock using Redis with unique token ownership and safe TTL.
    Protects concurrent learners from submitting simultaneous booking attempts for the same mentor slot.
    """

    def __init__(
        self,
        lock_key: str,
        ttl_seconds: int | None = None,
        timeout_seconds: float | None = None,
        retry_delay_seconds: float = 0.05
    ):
        self.lock_key = lock_key
        self.ttl_seconds = ttl_seconds or getattr(settings, "DISTRIBUTED_LOCK_TTL_SECONDS", 10)
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else getattr(settings, "DISTRIBUTED_LOCK_TIMEOUT_SECONDS", 2.0)
        self.retry_delay_seconds = retry_delay_seconds
        self.token = str(uuid.uuid4())
        self.acquired = False

    def acquire(self) -> bool:
        if not getattr(settings, "DISTRIBUTED_LOCK_ENABLED", True):
            return True

        start_time = time.time()
        while True:
            # Atomic set if not exists with TTL
            ok = redis_client.set_nx(self.lock_key, self.token, ex=self.ttl_seconds)
            if ok:
                self.acquired = True
                log_structured_event(
                    "booking_lock_acquired",
                    lock_key=self.lock_key,
                    token=self.token,
                    ttl=self.ttl_seconds
                )
                return True

            if (time.time() - start_time) >= self.timeout_seconds:
                log_structured_event(
                    "booking_lock_timeout",
                    lock_key=self.lock_key,
                    timeout=self.timeout_seconds
                )
                return False

            time.sleep(self.retry_delay_seconds)

    def release(self) -> bool:
        if not self.acquired:
            return True

        try:
            res = redis_client.eval_lua(LUA_RELEASE_LOCK, 1, self.lock_key, self.token)
            log_structured_event(
                "booking_lock_released",
                lock_key=self.lock_key,
                success=bool(res)
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
    start_time: datetime | str,
    end_time: datetime | str,
    ttl_seconds: int | None = None,
    timeout_seconds: float | None = None
) -> Generator[RedisDistributedLock, None, None]:
    """
    Context manager for distributed booking lock around mentor slots.
    Raises HTTP 409 Conflict if lock cannot be acquired within timeout.
    """
    lock_key = generate_slot_lock_key(mentor_id, start_time, end_time)
    lock = RedisDistributedLock(
        lock_key=lock_key,
        ttl_seconds=ttl_seconds,
        timeout_seconds=timeout_seconds
    )

    acquired = lock.acquire()
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot was just booked by another learner. Please choose another time."
        )

    try:
        yield lock
    finally:
        lock.release()
