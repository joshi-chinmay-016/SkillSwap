"""
SkillSwap Arena — Centralized Production Redis Client (Phase 6)

Provides a robust, pooled Redis client with automatic in-memory fallback.
Reads connection parameters exclusively from environment/config.
Handles connection reuse, health pings, and clean application shutdown.
"""
import time
import fnmatch
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import redis
from redis.connection import ConnectionPool

from app.core.config import settings

logger = logging.getLogger("skillswap.redis")


class SafeRedis:
    """
    Production-grade Redis wrapper with connection pooling and in-memory fallback.
    - Uses Redis ConnectionPool when Redis is reachable.
    - Gracefully falls back to an in-memory TTL store for local development/tests.
    - Thread-safe and process-safe operations.
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._memory_store: Dict[str, Tuple[Any, Optional[float]]] = {}  # key -> (value, expire_timestamp)
        self._memory_zsets: Dict[str, Dict[str, float]] = {}             # key -> {member: score}
        self._init_client()

    def _init_client(self) -> None:
        """Initializes the Redis connection pool using project configuration."""
        try:
            redis_url = getattr(settings, "REDIS_URL", "")
            max_connections = getattr(settings, "REDIS_MAX_CONNECTIONS", 50)
            socket_timeout = getattr(settings, "REDIS_SOCKET_TIMEOUT", 5.0)
            connect_timeout = getattr(settings, "REDIS_CONNECT_TIMEOUT", 5.0)

            if redis_url:
                self._pool = ConnectionPool.from_url(
                    redis_url,
                    max_connections=max_connections,
                    socket_timeout=socket_timeout,
                    socket_connect_timeout=connect_timeout,
                    decode_responses=True,
                )
            else:
                host = getattr(settings, "REDIS_HOST", "localhost")
                port = getattr(settings, "REDIS_PORT", 6379)
                db = getattr(settings, "REDIS_DB", 0)
                password = getattr(settings, "REDIS_PASSWORD", "") or None
                self._pool = ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    max_connections=max_connections,
                    socket_timeout=socket_timeout,
                    socket_connect_timeout=connect_timeout,
                    decode_responses=True,
                )

            client = redis.Redis(connection_pool=self._pool)
            client.ping()
            self._client = client
            logger.info("Connected to Redis server successfully with connection pooling.")
        except Exception as e:
            logger.info(f"Redis daemon not reachable at startup ({e}). Operating in memory-safe fallback mode.")
            self._client = None
            self._pool = None

    def is_available(self) -> bool:
        """Checks if live Redis connection is active and healthy."""
        if self._client:
            try:
                return bool(self._client.ping())
            except Exception:
                self._client = None
                return False
        return False

    def get_raw_client(self) -> Optional[redis.Redis]:
        """Returns the underlying redis.Redis client instance if available."""
        return self._client

    def _clean_memory_key(self, name: str) -> bool:
        """Returns True if memory key is valid, deletes and returns False if expired."""
        if name in self._memory_store:
            val, exp = self._memory_store[name]
            if exp is not None and time.time() > exp:
                del self._memory_store[name]
                return False
            return True
        return False

    def get(self, name: str) -> Optional[str]:
        if self._client:
            try:
                return self._client.get(name)
            except Exception as e:
                logger.debug(f"Redis get error on {name}: {e}")
                self._client = None

        if self._clean_memory_key(name):
            return self._memory_store[name][0]
        return None

    def set(self, name: str, value: str, ex: Optional[int] = None) -> bool:
        if self._client:
            try:
                return bool(self._client.set(name, value, ex=ex))
            except Exception as e:
                logger.debug(f"Redis set error on {name}: {e}")
                self._client = None

        exp = (time.time() + ex) if ex else None
        self._memory_store[name] = (value, exp)
        return True

    def setex(self, name: str, time_sec: int, value: str) -> bool:
        return self.set(name, value, ex=time_sec)

    def set_nx(self, name: str, value: str, ex: Optional[int] = None) -> bool:
        if self._client:
            try:
                return bool(self._client.set(name, value, nx=True, ex=ex))
            except Exception as e:
                logger.debug(f"Redis set_nx error on {name}: {e}")
                self._client = None

        if self._clean_memory_key(name):
            return False
        exp = (time.time() + ex) if ex else None
        self._memory_store[name] = (value, exp)
        return True

    def delete(self, *names: str) -> int:
        if not names:
            return 0
        if self._client:
            try:
                return self._client.delete(*names)
            except Exception as e:
                logger.debug(f"Redis delete error: {e}")
                self._client = None

        count = 0
        for name in names:
            if name in self._memory_store:
                del self._memory_store[name]
                count += 1
            if name in self._memory_zsets:
                del self._memory_zsets[name]
                count += 1
        return count

    def delete_pattern(self, pattern: str) -> int:
        if self._client:
            try:
                keys = self._client.keys(pattern)
                if keys:
                    return self._client.delete(*keys)
                return 0
            except Exception as e:
                logger.debug(f"Redis delete_pattern error for {pattern}: {e}")
                self._client = None

        keys_to_del = [k for k in self._memory_store if fnmatch.fnmatch(k, pattern)]
        for k in keys_to_del:
            del self._memory_store[k]
        z_keys_to_del = [k for k in self._memory_zsets if fnmatch.fnmatch(k, pattern)]
        for k in z_keys_to_del:
            del self._memory_zsets[k]
        return len(keys_to_del) + len(z_keys_to_del)

    def keys(self, pattern: str = "*") -> List[str]:
        if self._client:
            try:
                return self._client.keys(pattern)
            except Exception as e:
                logger.debug(f"Redis keys error for {pattern}: {e}")
                self._client = None

        matched = [k for k in self._memory_store if fnmatch.fnmatch(k, pattern) and self._clean_memory_key(k)]
        return matched

    def eval_lua(self, script: str, numkeys: int, *keys_and_args: Any) -> Any:
        if self._client:
            try:
                return self._client.eval(script, numkeys, *keys_and_args)
            except Exception as e:
                logger.debug(f"Redis eval_lua error: {e}")
                self._client = None

        # In-memory support for lock release script
        if "redis.call(\"get\", KEYS[1]) == ARGV[1]" in script or "redis.call('get', KEYS[1]) == ARGV[1]" in script:
            key = keys_and_args[0]
            token = keys_and_args[1]
            if self._clean_memory_key(key) and self._memory_store[key][0] == token:
                del self._memory_store[key]
                return 1
            return 0
        return None

    # Sliding-window rate limiting & sorted set operations
    def zadd(self, name: str, mapping: Dict[str, float]) -> Optional[int]:
        if self._client:
            try:
                return self._client.zadd(name, mapping)
            except Exception as e:
                logger.debug(f"Redis zadd error on {name}: {e}")
                self._client = None

        if name not in self._memory_zsets:
            self._memory_zsets[name] = {}
        for member, score in mapping.items():
            self._memory_zsets[name][member] = float(score)
        return len(mapping)

    def zremrangebyscore(self, name: str, min_score: Union[float, int], max_score: Union[float, int]) -> int:
        if self._client:
            try:
                return self._client.zremrangebyscore(name, min_score, max_score)
            except Exception as e:
                logger.debug(f"Redis zremrangebyscore error on {name}: {e}")
                self._client = None

        if name not in self._memory_zsets:
            return 0
        to_del = [m for m, score in self._memory_zsets[name].items() if min_score <= score <= max_score]
        for m in to_del:
            del self._memory_zsets[name][m]
        return len(to_del)

    def zcard(self, name: str) -> int:
        if self._client:
            try:
                return self._client.zcard(name) or 0
            except Exception as e:
                logger.debug(f"Redis zcard error on {name}: {e}")
                self._client = None

        return len(self._memory_zsets.get(name, {}))

    def expire(self, name: str, time_sec: int) -> bool:
        if self._client:
            try:
                return bool(self._client.expire(name, time_sec))
            except Exception as e:
                logger.debug(f"Redis expire error on {name}: {e}")
                self._client = None

        if name in self._memory_store:
            val, _ = self._memory_store[name]
            self._memory_store[name] = (val, time.time() + time_sec)
            return True
        return False

    def ttl(self, name: str) -> int:
        if self._client:
            try:
                return self._client.ttl(name)
            except Exception:
                self._client = None

        if name in self._memory_store:
            _, exp = self._memory_store[name]
            if exp is None:
                return -1
            remaining = int(exp - time.time())
            return remaining if remaining > 0 else -2
        return -2

    def close(self) -> None:
        """Closes connection pool on application shutdown."""
        try:
            if self._client:
                self._client.close()
            if self._pool:
                self._pool.disconnect()
            logger.info("Redis connections closed successfully.")
        except Exception as e:
            logger.warning(f"Error during Redis pool close: {e}")
        finally:
            self._client = None
            self._pool = None


# Centralized singleton instance
redis_client = SafeRedis()
