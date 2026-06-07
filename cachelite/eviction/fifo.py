"""FIFO eviction — deque-based insertion order."""

from __future__ import annotations

from collections import deque

from ..errors import CacheEmptyError
from .base import EvictionPolicy


class FIFOPolicy(EvictionPolicy):
    """First In, First Out.

    A deque records insertion order. Deletes are handled lazily: removed keys
    stay in the deque but are tracked in a "live" set, so evict() skips any
    tombstoned entries. This keeps every operation O(1) amortized.
    """

    def __init__(self) -> None:
        self._order: "deque[str]" = deque()
        self._keys: set[str] = set()

    def on_insert(self, key: str) -> None:
        if key in self._keys:
            return  # re-set keeps original FIFO position
        self._order.append(key)
        self._keys.add(key)

    def on_access(self, key: str) -> None:
        pass  # FIFO ignores access order

    def on_remove(self, key: str) -> None:
        self._keys.discard(key)  # tombstone; physically dropped during evict

    def evict(self) -> str:
        while self._order:
            key = self._order.popleft()
            if key in self._keys:
                self._keys.discard(key)
                return key
        raise CacheEmptyError("nothing to evict")

    def clear(self) -> None:
        self._order.clear()
        self._keys.clear()

    def __len__(self) -> int:
        return len(self._keys)

    def __contains__(self, key: str) -> bool:
        return key in self._keys
