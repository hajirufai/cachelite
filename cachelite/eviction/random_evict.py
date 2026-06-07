"""Random eviction — uniform random victim selection in O(1)."""

from __future__ import annotations

import random

from ..errors import CacheEmptyError
from .base import EvictionPolicy


class RandomPolicy(EvictionPolicy):
    """Evict a uniformly random key.

    Trick for O(1) removal of an arbitrary element: keep keys in a list plus a
    key->index map. To remove index ``i``, swap the element at ``i`` with the
    last element, fix the moved element's index, then pop the tail. No shifting.
    """

    def __init__(self, rng: "random.Random | None" = None) -> None:
        self._keys: list[str] = []
        self._index: dict[str, int] = {}
        self._rng = rng or random.Random()

    def on_insert(self, key: str) -> None:
        if key in self._index:
            return
        self._index[key] = len(self._keys)
        self._keys.append(key)

    def on_access(self, key: str) -> None:
        pass  # random policy is access-agnostic

    def _remove_at(self, idx: int) -> str:
        key = self._keys[idx]
        last = self._keys[-1]
        self._keys[idx] = last
        self._index[last] = idx
        self._keys.pop()
        del self._index[key]
        return key

    def on_remove(self, key: str) -> None:
        idx = self._index.get(key)
        if idx is not None:
            self._remove_at(idx)

    def evict(self) -> str:
        if not self._keys:
            raise CacheEmptyError("nothing to evict")
        idx = self._rng.randrange(len(self._keys))
        return self._remove_at(idx)

    def clear(self) -> None:
        self._keys.clear()
        self._index.clear()

    def __len__(self) -> int:
        return len(self._keys)

    def __contains__(self, key: str) -> bool:
        return key in self._index
