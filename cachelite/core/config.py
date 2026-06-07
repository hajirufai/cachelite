"""Cache configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..types import EvictionPolicy


@dataclass
class CacheConfig:
    """Tunable parameters for a Cache instance.

    Attributes:
        max_items: Hard cap on the number of stored entries. None == unlimited
            (still bounded by max_bytes if that is set).
        max_bytes: Soft memory budget in bytes. When exceeded, entries are
            evicted until the cache fits. None == no byte budget.
        policy: Which eviction policy to use when capacity is reached.
        default_ttl: Default time-to-live (seconds) applied to set() calls that
            don't pass an explicit ttl. None == entries never expire by default.
        active_expiry: Run a background sweeper thread for proactive expiry.
        sweep_interval: How often (seconds) the active sweeper runs.
        sweep_sample: How many random keys the sweeper checks per pass.
        num_stripes: Lock stripes for concurrency. 1 == single global lock.
        thread_safe: Wrap operations in locks. Disable for single-threaded use
            to shave overhead.
    """

    max_items: Optional[int] = 1000
    max_bytes: Optional[int] = None
    policy: EvictionPolicy = EvictionPolicy.LRU
    default_ttl: Optional[float] = None
    active_expiry: bool = False
    sweep_interval: float = 1.0
    sweep_sample: int = 20
    num_stripes: int = 16
    thread_safe: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.policy, str):
            self.policy = EvictionPolicy.from_string(self.policy)
        if self.max_items is not None and self.max_items <= 0:
            raise ValueError("max_items must be positive or None")
        if self.max_bytes is not None and self.max_bytes <= 0:
            raise ValueError("max_bytes must be positive or None")
        if self.max_items is None and self.max_bytes is None:
            raise ValueError("at least one of max_items or max_bytes must be set")
        if self.num_stripes < 1:
            raise ValueError("num_stripes must be >= 1")
        if self.default_ttl is not None and self.default_ttl <= 0:
            raise ValueError("default_ttl must be positive or None")
