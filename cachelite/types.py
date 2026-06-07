"""Core data types shared across CacheLite."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EvictionPolicy(str, Enum):
    """Supported eviction policies."""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    RANDOM = "random"

    @classmethod
    def from_string(cls, name: str) -> "EvictionPolicy":
        try:
            return cls(name.lower())
        except ValueError as exc:  # pragma: no cover - thin wrapper
            valid = ", ".join(p.value for p in cls)
            raise ValueError(f"unknown policy {name!r}; valid: {valid}") from exc


@dataclass
class CacheEntry:
    """A single stored value plus its metadata.

    Timestamps use a monotonic clock so they are immune to wall-clock jumps
    (NTP corrections, daylight saving, manual clock changes).
    """

    key: str
    value: Any
    size_bytes: int = 0
    created_at: float = field(default_factory=time.monotonic)
    accessed_at: float = field(default_factory=time.monotonic)
    frequency: int = 0
    expires_at: Optional[float] = None  # monotonic deadline, None == never

    def is_expired(self, now: Optional[float] = None) -> bool:
        if self.expires_at is None:
            return False
        now = time.monotonic() if now is None else now
        return now >= self.expires_at

    def remaining_ttl(self, now: Optional[float] = None) -> Optional[float]:
        if self.expires_at is None:
            return None
        now = time.monotonic() if now is None else now
        return max(0.0, self.expires_at - now)

    def touch(self, now: Optional[float] = None) -> None:
        self.accessed_at = time.monotonic() if now is None else now
        self.frequency += 1
