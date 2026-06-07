"""In-memory storage backend.

The Cache holds its primary dict directly for speed, but this thin wrapper
exists so storage could be swapped (e.g. for a disk-backed variant) without
touching cache logic. It implements the minimal mapping surface the cache
relies on.
"""

from __future__ import annotations

from typing import Iterator, Optional

from ..types import CacheEntry


class MemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[CacheEntry]:
        return self._data.get(key)

    def put(self, key: str, entry: CacheEntry) -> None:
        self._data[key] = entry

    def pop(self, key: str) -> Optional[CacheEntry]:
        return self._data.pop(key, None)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def clear(self) -> None:
        self._data.clear()
