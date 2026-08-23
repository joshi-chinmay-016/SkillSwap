"""
SkillSwap Arena — Redis Core Interface (Phase 6 Forwarding Layer)

Re-exports the production-grade SafeRedis singleton and class from app.infrastructure.redis
to maintain 100% backward compatibility for all existing Phase 1–5 services and test fixtures.
"""
from app.infrastructure.redis.client import redis_client, SafeRedis

__all__ = ["redis_client", "SafeRedis"]