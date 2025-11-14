"""Integration models for database sync"""

from enum import Enum


class SyncStrategy(Enum):
    """Database synchronization strategies"""

    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    READ_THROUGH = "read_through"
    CACHE_ASIDE = "cache_aside"
