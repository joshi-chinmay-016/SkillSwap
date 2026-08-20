import redis

class SafeRedis:
    def __init__(self):
        self._client = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
            socket_timeout=0.2,
            socket_connect_timeout=0.2
        )

    def get(self, name):
        try:
            return self._client.get(name)
        except Exception:
            return None

    def set(self, name, value, ex=None):
        try:
            return self._client.set(name, value, ex=ex)
        except Exception:
            return None

    def setex(self, name, time, value):
        try:
            return self._client.set(name, value, ex=time)
        except Exception:
            return None

    def delete(self, *names):
        try:
            return self._client.delete(*names)
        except Exception:
            return None

redis_client = SafeRedis()