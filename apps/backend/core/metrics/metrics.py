"""
Application Metrics Module - Production Monitoring
"""

import time
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# GPT-4.1 metrics
GPT41_REQUESTS = Counter("gpt41_requests_total", "Total GPT-4.1 API requests", ["model", "status"])

GPT41_TOKENS = Counter("gpt41_tokens_used_total", "Total tokens used", ["model"])

GPT41_COST = Counter("gpt41_cost_dollars_total", "Total cost in dollars", ["model"])

GPT41_LATENCY = Histogram("gpt41_response_time_seconds", "GPT-4.1 response time", ["model"])

# Database metrics
DB_CONNECTIONS = Gauge("database_connections_active", "Active database connections")

DB_QUERY_DURATION = Histogram(
    "database_query_duration_seconds", "Database query duration", ["query_type"]
)

# Cache metrics
CACHE_HITS = Counter("cache_hits_total", "Total cache hits", ["cache_type"])

CACHE_MISSES = Counter("cache_misses_total", "Total cache misses", ["cache_type"])

# Business metrics
USER_ACTIVITY = Counter("user_activity_total", "User activity events", ["user_id", "action"])

REVENUE_TOTAL = Counter("revenue_dollars_total", "Total revenue in dollars", ["product"])

# Security metrics
AUTH_FAILURES = Counter("auth_failures_total", "Authentication failures", ["reason"])

SUSPICIOUS_REQUESTS = Counter("suspicious_requests_total", "Suspicious requests detected", ["type"])


def track_request(method: str, endpoint: str):
    """Decorator to track HTTP requests"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_COUNT.labels(method, endpoint, status).inc()
                REQUEST_DURATION.labels(method, endpoint).observe(duration)

        return wrapper

    return decorator


def track_gpt41_request(model: str):
    """Track GPT-4.1 API request"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)

                # Track tokens and cost
                if "usage" in result:
                    tokens = result["usage"].get("total_tokens", 0)
                    GPT41_TOKENS.labels(model).inc(tokens)

                    # Calculate cost (example rates)
                    cost = tokens * 0.00003  # $0.03 per 1K tokens
                    GPT41_COST.labels(model).inc(cost)

                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                GPT41_REQUESTS.labels(model, status).inc()
                GPT41_LATENCY.labels(model).observe(duration)

        return wrapper

    return decorator


def track_db_query(query_type: str):
    """Decorator to track database query performance"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                DB_QUERY_DURATION.labels(query_type).observe(duration)

        return wrapper

    return decorator


def get_metrics():
    """Get current metrics in Prometheus format"""
    return generate_latest()
