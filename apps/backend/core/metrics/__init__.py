"""
Application Metrics Module

Re-exports all metrics and tracking functions from metrics.py
"""

from apps.backend.core.metrics.metrics import (
    # Request metrics
    REQUEST_COUNT,
    REQUEST_DURATION,
    # GPT-4.1 metrics
    GPT41_REQUESTS,
    GPT41_TOKENS,
    GPT41_COST,
    GPT41_LATENCY,
    # Database metrics
    DB_CONNECTIONS,
    DB_QUERY_DURATION,
    # Cache metrics
    CACHE_HITS,
    CACHE_MISSES,
    # Business metrics
    USER_ACTIVITY,
    REVENUE_TOTAL,
    # Security metrics
    AUTH_FAILURES,
    SUSPICIOUS_REQUESTS,
    # Tracking decorators
    track_request,
    track_gpt41_request,
    track_db_query,
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
