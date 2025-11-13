"""
Application Metrics Module

Re-exports all metrics and tracking functions from metrics.py
"""

from apps.backend.core.metrics.metrics import (  # Request metrics; GPT-4.1 metrics; Database metrics; Cache metrics; Business metrics; Security metrics; Tracking decorators
    AUTH_FAILURES,
    CACHE_HITS,
    CACHE_MISSES,
    DB_CONNECTIONS,
    DB_QUERY_DURATION,
    GPT41_COST,
    GPT41_LATENCY,
    GPT41_REQUESTS,
    GPT41_TOKENS,
    REQUEST_COUNT,
    REQUEST_DURATION,
    REVENUE_TOTAL,
    SUSPICIOUS_REQUESTS,
    USER_ACTIVITY,
    track_db_query,
    track_gpt41_request,
    track_request,
)

__all__ = [
    "REQUEST_COUNT",
    "REQUEST_DURATION",
    "GPT41_REQUESTS",
    "GPT41_TOKENS",
    "GPT41_COST",
    "GPT41_LATENCY",
    "DB_CONNECTIONS",
    "DB_QUERY_DURATION",
    "CACHE_HITS",
    "CACHE_MISSES",
    "USER_ACTIVITY",
    "REVENUE_TOTAL",
    "AUTH_FAILURES",
    "SUSPICIOUS_REQUESTS",
    "track_request",
    "track_gpt41_request",
    "track_db_query",
]
