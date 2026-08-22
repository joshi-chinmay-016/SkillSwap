import time
import logging
from typing import Any, Dict, Tuple
import redis
from app.core.config import settings

logger = logging.getLogger("skillswap.redis")


class SafeRedis:
    """
    Production-oriented Redis wrapper with in-memory fallback.
    When a live Redis server is reachable, executes commands on Redis.
    When Redis is unavailable or unconfigured, falls back seamlessly to an
    in-memory structure to maintain idempotency, sliding-window rate limiting,
    and distributed lock simulation in local dev and testing.
    """
    def __init__(self):
        self._client: redis.Redis | None = None
        self._memory_store: Dict[str, Tuple[Any, float | None]] = {}  # key -> (value, expire_timestamp)
        self._memory_zsets: Dict[str, Dict[str, float]] = {}          # key -> {member: score}
        self._init_client()

    def _init_client(self):
        try:
            redis_url = getattr(settings, "REDIS_URL", "")
            if redis_url:
                c = redis.Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=0.5,
                    socket_connect_timeout=0.5
                )
                c.ping()
                self._client = c
            else:
                host = getattr(settings, "REDIS_HOST", "localhost")
                port = getattr(settings, "REDIS_PORT", 6379)
                db = getattr(settings, "REDIS_DB", 0)
                password = getattr(settings, "REDIS_PASSWORD", "") or None
                c = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=True,
                    socket_timeout=0.5,
                    socket_connect_timeout=0.5
                )
                c.ping()
                self._client = c
        except Exception as e:
            logger.info(f"Redis daemon not reachable at startup ({e}). Operating in memory-safe fallback mode.")
            self._client = None

    def is_available(self) -> bool:
        if self._client:
            try:
                return bool(self._client.ping())
            except Exception:
                self._client = None
                return False
        return False

    def _clean_memory_key(self, name: str) -> bool:
        """Returns True if key is valid/exists, False if expired/not found."""
        if name in self._memory_store:
            val, exp = self._memory_store[name]
            if exp is not None and time.time() > exp:
                del self._memory_store[name]
                return False
            return True
        return False

    def get(self, name: str) -> str | None:
        if self._client:
            try:
                return self._client.get(name)
            except Exception as e:
                logger.debug(f"Redis get error on key {name}: {e}")
                self._client = None

        # In-memory fallback
        if self._clean_memory_key(name):
            return self._memory_store[name][0]
        return None

    def set(self, name: str, value: str, ex: int | None = None) -> bool:
        if self._client:
            try:
                return bool(self._client.set(name, value, ex=ex))
            except Exception as e:
                logger.debug(f"Redis set error on key {name}: {e}")
                self._client = None

        exp = (time.time() + ex) if ex else None
        self._memory_store[name] = (value, exp)
        return True

    def setex(self, name: str, time_sec: int, value: str) -> bool:
        return self.set(name, value, ex=time_sec)

    def set_nx(self, name: str, value: str, ex: int | None = None) -> bool:
        if self._client:
            try:
                return bool(self._client.set(name, value, nx=True, ex=ex))
            except Exception as e:
                logger.debug(f"Redis set_nx error on key {name}: {e}")
                self._client = None

        # In-memory NX
        if self._clean_memory_key(name):
            return False
        exp = (time.time() + ex) if ex else None
        self._memory_store[name] = (value, exp)
        return True

    def delete(self, *names: str) -> int:
        if self._client:
            try:
                if names:
                    return self._client.delete(*names)
                return 0
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
        import fnmatch
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
        return len(keys_to_del)

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

    # Sliding-window rate limit & sorted set operations
    def zadd(self, name: str, mapping: dict) -> int | None:
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

    def zremrangebyscore(self, name: str, min_score: float | int, max_score: float | int) -> int:
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


redis_client = SafeRedis()