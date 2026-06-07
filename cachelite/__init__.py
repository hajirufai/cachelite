"""CacheLite — a high-performance, zero-dependency in-memory cache engine.

Hand-rolled eviction policies (LRU, LFU, FIFO, Random), TTL expiry, thread
safety, snapshot persistence, statistics, pattern invalidation, an HTTP API
and a CLI — all from the Python standard library.

Quick start::

    from cachelite import Cache

    cache = Cache(max_items=1000, policy="lru", default_ttl=60)
    cache.set("user:1", {"name": "Ada"})
    print(cache.get("user:1"))
"""

from .core.cache import Cache
from .core.config import CacheConfig
from .decorators import cached
from .errors import (CacheEmptyError, CacheError, CacheFullError,
                     CacheKeyError, SnapshotError, UnknownPolicyError)
from .stats import CacheStats
from .types import CacheEntry, EvictionPolicy

__version__ = "1.0.0"

__all__ = [
    "Cache",
    "CacheConfig",
    "CacheStats",
    "CacheEntry",
    "EvictionPolicy",
    "cached",
    "CacheError",
    "CacheEmptyError",
    "CacheFullError",
    "CacheKeyError",
    "SnapshotError",
    "UnknownPolicyError",
    "__version__",
]
