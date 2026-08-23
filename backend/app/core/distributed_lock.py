"""
SkillSwap Arena — Distributed Lock Core Interface (Phase 6 Forwarding Layer)

Re-exports distributed locks and context managers from app.infrastructure.redis.locks
for backward compatibility across all existing booking logic and test suites.
"""
from app.infrastructure.redis.locks import (
    LUA_RELEASE_LOCK,
    RedisDistributedLock,
    distributed_booking_lock,
    distributed_session_lock,
)
from app.infrastructure.redis.keys import booking_lock_key as generate_slot_lock_key

__all__ = [
    "LUA_RELEASE_LOCK",
    "generate_slot_lock_key",
    "RedisDistributedLock",
    "distributed_booking_lock",
    "distributed_session_lock",
]
