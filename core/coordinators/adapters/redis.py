import os, json, time
from typing import Optional, Any, Dict

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

DEFAULT_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

class RedisAdapter:
    """Thin Redis wrapper used by the terminal task queue (termq).
    Keeps usage minimal to avoid coupling.
    """

    def __init__(self, url: Optional[str] = None):
        self.url = url or DEFAULT_REDIS_URL
        if redis is None:
            raise RuntimeError("redis-py not installed. Please `pip install redis`.')
        self.r = redis.Redis.from_url(self.url, decode_responses=True)

    def ping(self) -> bool:
        try:
            return bool(self.r.ping())
        except Exception:
            return False

    def now_ms(self) -> int:
        return int(time.time() * 1000)

    def json_set(self, key: str, value: Dict[str, Any], ex: Optional[int] = None):
        pipe = self.r.pipeline()
        pipe.set(key, json.dumps(value))
        if ex:
            pipe.expire(key, ex)
        pipe.execute()

    def json_get(self, key: str) -> Optional[Dict[str, Any]]:
        v = self.r.get(key)
        return json.loads(v) if v else None
