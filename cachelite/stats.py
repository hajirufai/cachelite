"""Cache statistics."""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass


@dataclass
class CacheStats:
    """A point-in-time snapshot of cache counters."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    sets: int = 0
    deletes: int = 0
    current_items: int = 0
    current_bytes: int = 0
    max_items: int = 0
    max_bytes: int = 0
    uptime_seconds: float = 0.0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    @property
    def miss_rate(self) -> float:
        total = self.hits + self.misses
        return self.misses / total if total else 0.0

    @property
    def eviction_rate(self) -> float:
        return self.evictions / self.sets if self.sets else 0.0

    def as_dict(self) -> dict:
        d = asdict(self)
        d["hit_rate"] = round(self.hit_rate, 4)
        d["miss_rate"] = round(self.miss_rate, 4)
        d["eviction_rate"] = round(self.eviction_rate, 4)
        return d


class StatsCollector:
    """Thread-safe mutable counters that snapshot into a ``CacheStats``."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started = time.monotonic()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        self.sets = 0
        self.deletes = 0

    def record_hit(self, n: int = 1) -> None:
        with self._lock:
            self.hits += n

    def record_miss(self, n: int = 1) -> None:
        with self._lock:
            self.misses += n

    def record_eviction(self, n: int = 1) -> None:
        with self._lock:
            self.evictions += n

    def record_expiration(self, n: int = 1) -> None:
        with self._lock:
            self.expirations += n

    def record_set(self, n: int = 1) -> None:
        with self._lock:
            self.sets += n

    def record_delete(self, n: int = 1) -> None:
        with self._lock:
            self.deletes += n

    def snapshot(self, current_items: int, current_bytes: int,
                 max_items: int, max_bytes: int) -> CacheStats:
        with self._lock:
            return CacheStats(
                hits=self.hits,
                misses=self.misses,
                evictions=self.evictions,
                expirations=self.expirations,
                sets=self.sets,
                deletes=self.deletes,
                current_items=current_items,
                current_bytes=current_bytes,
                max_items=max_items or 0,
                max_bytes=max_bytes or 0,
                uptime_seconds=round(time.monotonic() - self._started, 3),
            )

    def reset(self) -> None:
        with self._lock:
            self.hits = self.misses = self.evictions = 0
            self.expirations = self.sets = self.deletes = 0
            self._started = time.monotonic()
