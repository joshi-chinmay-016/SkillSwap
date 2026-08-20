import logging
import redis
from app.core.config import settings

logger = logging.getLogger("skillswap.redis")


class SafeRedis:
    def __init__(self):
        try:
            self._client = redis.Redis(
                host=getattr(settings, "REDIS_HOST", "localhost"),
                port=getattr(settings, "REDIS_PORT", 6379),
                db=getattr(settings, "REDIS_DB", 0),
                decode_responses=True,
                socket_timeout=0.5,
                socket_connect_timeout=0.5
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {e}")
            self._client = None

    def is_available(self) -> bool:
        try:
            return bool(self._client and self._client.ping())
        except Exception:
            return False

    def get(self, name: str):
        try:
            if not self._client:
                return None
            return self._client.get(name)
        except Exception as e:
            logger.debug(f"Redis get error on key {name}: {e}")
            return None

    def set(self, name: str, value: str, ex=None):
        try:
            if not self._client:
                return None
            return self._client.set(name, value, ex=ex)
        except Exception as e:
            logger.debug(f"Redis set error on key {name}: {e}")
            return None

    def setex(self, name: str, time: int, value: str):
        try:
            if not self._client:
                return None
            return self._client.set(name, value, ex=time)
        except Exception as e:
            logger.debug(f"Redis setex error on key {name}: {e}")
            return None

    def delete(self, *names):
        try:
            if not self._client or not names:
                return 0
            return self._client.delete(*names)
        except Exception as e:
            logger.debug(f"Redis delete error: {e}")
            return 0

    def delete_pattern(self, pattern: str) -> int:
        """Deletes all keys matching the glob pattern safely."""
        try:
            if not self._client:
                return 0
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Redis delete_pattern error for {pattern}: {e}")
            return 0

    # Sliding-window rate limit operations
    def zadd(self, name: str, mapping: dict):
        try:
            if not self._client:
                return None
            return self._client.zadd(name, mapping)
        except Exception as e:
            logger.debug(f"Redis zadd error on {name}: {e}")
            return None

    def zremrangebyscore(self, name: str, min_score, max_score):
        try:
            if not self._client:
                return 0
            return self._client.zremrangebyscore(name, min_score, max_score)
        except Exception as e:
            logger.debug(f"Redis zremrangebyscore error on {name}: {e}")
            return 0

    def zcard(self, name: str) -> int:
        try:
            if not self._client:
                return 0
            return self._client.zcard(name) or 0
        except Exception as e:
            logger.debug(f"Redis zcard error on {name}: {e}")
            return 0

    def expire(self, name: str, time: int):
        try:
            if not self._client:
                return False
            return self._client.expire(name, time)
        except Exception as e:
            logger.debug(f"Redis expire error on {name}: {e}")
            return False


redis_client = SafeRedis()