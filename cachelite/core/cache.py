"""The Cache — the main public interface tying everything together."""

from __future__ import annotations

import threading
import time
from typing import Any, Iterator, Optional, Union

from ..errors import CacheFullError
from ..eviction import make_policy
from ..events import (CacheEvents, ON_CLEAR, ON_DELETE, ON_EVICT, ON_EXPIRE,
                      ON_HIT, ON_MISS, ON_SET)
from ..patterns import filter_keys, matches
from ..stats import CacheStats, StatsCollector
from ..storage.snapshot import load_snapshot, save_snapshot
from ..sync import StripedLock
from ..types import CacheEntry, EvictionPolicy
from ..utils import estimate_size, validate_key
from .config import CacheConfig

_MISSING = object()


class Cache:
    """A thread-safe, bounded, in-memory cache.

    Example::

        cache = Cache(max_items=1000, policy="lru", default_ttl=60)
        cache.set("user:1", {"name": "Ada"})
        cache.get("user:1")          # -> {"name": "Ada"}
        cache.invalidate("user:*")   # bulk delete by glob

    All public methods are safe to call from multiple threads. Internally the
    keyspace is sharded across lock stripes; whole-cache operations take a
    global write lock.
    """

    def __init__(
        self,
        max_items: Optional[int] = 1000,
        max_bytes: Optional[int] = None,
        policy: Union[str, EvictionPolicy] = "lru",
        default_ttl: Optional[float] = None,
        config: Optional[CacheConfig] = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = CacheConfig(
                max_items=max_items,
                max_bytes=max_bytes,
                policy=policy,
                default_ttl=default_ttl,
                **kwargs,
            )
        self.config = config
        self._store: dict[str, CacheEntry] = {}
        self._policy = make_policy(config.policy)
        self._stats = StatsCollector()
        self.events = CacheEvents()
        self._current_bytes = 0
        # A single global lock guards the shared maps (store, policy, byte
        # counter). Striped locking is exposed for callers that want
        # key-level concurrency on top, but the structural invariants live
        # under this one lock to stay correct and simple.
        self._lock = threading.RLock()
        self._stripes = StripedLock(config.num_stripes)
        self._active = None
        if config.active_expiry:
            from ..expiry.active import ActiveExpiry

            self._active = ActiveExpiry(
                self, interval=config.sweep_interval, sample_size=config.sweep_sample
            )
            self._active.start()

    # ------------------------------------------------------------------ core

    def get(self, key: str, default: Any = None) -> Any:
        validate_key(key)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._stats.record_miss()
                self.events.emit(ON_MISS, key)
                return default
            if entry.is_expired():
                self._remove_locked(key, expired=True)
                self._stats.record_miss()
                self.events.emit(ON_MISS, key)
                return default
            entry.touch()
            self._policy.on_access(key)
            self._stats.record_hit()
            self.events.emit(ON_HIT, key, entry.value)
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        validate_key(key)
        if ttl is None:
            ttl = self.config.default_ttl
        expires_at = (time.monotonic() + ttl) if ttl else None
        size = estimate_size(value)

        if self.config.max_bytes is not None and size > self.config.max_bytes:
            raise CacheFullError(
                f"value for {key!r} is {size} bytes, exceeds max_bytes "
                f"{self.config.max_bytes}"
            )

        with self._lock:
            old = self._store.get(key)
            if old is not None:
                self._current_bytes -= old.size_bytes
                entry = old
                entry.value = value
                entry.size_bytes = size
                entry.expires_at = expires_at
                entry.created_at = time.monotonic()
                self._policy.on_access(key)
            else:
                entry = CacheEntry(
                    key=key, value=value, size_bytes=size, expires_at=expires_at
                )
                self._store[key] = entry
                self._policy.on_insert(key)
            self._current_bytes += size
            self._stats.record_set()
            self.events.emit(ON_SET, key, value)
            self._enforce_capacity_locked(protect=key)

    def delete(self, key: str) -> bool:
        validate_key(key)
        with self._lock:
            if key not in self._store:
                return False
            self._remove_locked(key)
            self._stats.record_delete()
            self.events.emit(ON_DELETE, key)
            return True

    def has(self, key: str) -> bool:
        validate_key(key)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                self._remove_locked(key, expired=True)
                return False
            return True

    __contains__ = has

    def clear(self) -> int:
        with self._lock:
            count = len(self._store)
            self._store.clear()
            self._policy.clear()
            self._current_bytes = 0
            self.events.emit(ON_CLEAR, "*")
            return count

    def size(self) -> int:
        """Number of live (non-expired) entries."""
        with self._lock:
            self._purge_expired_locked()
            return len(self._store)

    __len__ = size

    def keys(self, pattern: Optional[str] = None) -> list[str]:
        with self._lock:
            self._purge_expired_locked()
            if pattern is None:
                return list(self._store.keys())
            return list(filter_keys(self._store.keys(), pattern))

    def items(self) -> list[tuple[str, Any]]:
        with self._lock:
            self._purge_expired_locked()
            return [(k, e.value) for k, e in self._store.items()]

    def invalidate(self, pattern: str) -> int:
        with self._lock:
            victims = [k for k in self._store if matches(k, pattern)]
            for key in victims:
                self._remove_locked(key)
                self._stats.record_delete()
                self.events.emit(ON_DELETE, key)
            return len(victims)

    # ------------------------------------------------------------------- ttl

    def ttl(self, key: str) -> Optional[float]:
        validate_key(key)
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                return None
            return entry.remaining_ttl()

    def touch(self, key: str, ttl: Optional[float] = None) -> bool:
        """Reset a key's TTL without changing its value."""
        validate_key(key)
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                return False
            if ttl is None:
                ttl = self.config.default_ttl
            entry.expires_at = (time.monotonic() + ttl) if ttl else None
            return True

    def expire(self, key: str, ttl: float) -> bool:
        """Set a key to expire ``ttl`` seconds from now."""
        return self.touch(key, ttl)

    def persist(self, key: str) -> bool:
        """Remove a key's TTL so it never expires."""
        validate_key(key)
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                return False
            entry.expires_at = None
            return True

    # -------------------------------------------------------------- stats/io

    def stats(self) -> CacheStats:
        with self._lock:
            return self._stats.snapshot(
                current_items=len(self._store),
                current_bytes=self._current_bytes,
                max_items=self.config.max_items or 0,
                max_bytes=self.config.max_bytes or 0,
            )

    def reset_stats(self) -> None:
        self._stats.reset()

    def snapshot(self, path: str, fmt: str = "json") -> int:
        with self._lock:
            self._purge_expired_locked()
            return save_snapshot(path, self._store, self.config, fmt=fmt)

    def restore(self, path: str) -> int:
        with self._lock:
            entries = load_snapshot(path)
            count = 0
            for entry in entries:
                if entry.is_expired():
                    continue
                self._store[entry.key] = entry
                self._policy.on_insert(entry.key)
                self._current_bytes += entry.size_bytes
                count += 1
            self._enforce_capacity_locked()
            return count

    # --------------------------------------------------------------- helpers

    def _remove_locked(self, key: str, expired: bool = False) -> None:
        entry = self._store.pop(key, None)
        if entry is None:
            return
        self._policy.on_remove(key)
        self._current_bytes -= entry.size_bytes
        if expired:
            self._stats.record_expiration()
            self.events.emit(ON_EXPIRE, key)

    def _enforce_capacity_locked(self, protect: Optional[str] = None) -> None:
        """Evict until we're within both item and byte budgets."""
        max_items = self.config.max_items
        max_bytes = self.config.max_bytes
        while True:
            over_items = max_items is not None and len(self._store) > max_items
            over_bytes = max_bytes is not None and self._current_bytes > max_bytes
            if not (over_items or over_bytes):
                break
            if len(self._store) <= 1:
                break
            victim = self._policy.evict()
            # never evict the key we just inserted to satisfy its own write
            if victim == protect:
                # put it back at the policy's MRU end and stop to avoid a loop
                self._policy.on_insert(victim)
                break
            entry = self._store.pop(victim, None)
            if entry is not None:
                self._current_bytes -= entry.size_bytes
                self._stats.record_eviction()
                self.events.emit(ON_EVICT, victim, entry.value)

    def _purge_expired_locked(self) -> int:
        expired = [k for k, e in self._store.items() if e.is_expired()]
        for key in expired:
            self._remove_locked(key, expired=True)
        return len(expired)

    # Hooks used by the active-expiry sweeper.
    def _sample_keys(self, n: int) -> list[str]:
        import random

        with self._lock:
            keys = list(self._store.keys())
        if len(keys) <= n:
            return keys
        return random.sample(keys, n)

    def _sweep_expired(self, keys: list[str]) -> int:
        removed = 0
        with self._lock:
            for key in keys:
                entry = self._store.get(key)
                if entry is not None and entry.is_expired():
                    self._remove_locked(key, expired=True)
                    removed += 1
        return removed

    def close(self) -> None:
        if self._active is not None:
            self._active.stop()

    def __enter__(self) -> "Cache":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def __repr__(self) -> str:
        return (
            f"Cache(policy={self.config.policy.value}, items={len(self._store)}, "
            f"max_items={self.config.max_items}, bytes={self._current_bytes})"
        )
