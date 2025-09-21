
# Redis client for security module
try:
    import redis
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )
except ImportError:
    redis_client = None

