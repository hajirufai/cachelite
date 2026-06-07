"""LFU eviction — frequency buckets with min-tracking for O(1) operations."""

from __future__ import annotations

from collections import OrderedDict

from ..errors import CacheEmptyError
from .base import EvictionPolicy


class LFUPolicy(EvictionPolicy):
    """Least Frequently Used, O(1) amortized.

    Three structures cooperate:
      * ``_key_freq``  : key -> its current access frequency
      * ``_freq_keys`` : freq -> OrderedDict of keys at that frequency. The
                         OrderedDict preserves insertion order so that, when
                         two keys share the lowest frequency, we drop the
                         *oldest* one (LRU tie-break).
      * ``_min_freq``  : the smallest frequency currently in use, so evict()
                         never has to scan.
    """

    def __init__(self) -> None:
        self._key_freq: dict[str, int] = {}
        self._freq_keys: dict[int, "OrderedDict[str, None]"] = {}
        self._min_freq = 0

    def on_insert(self, key: str) -> None:
        if key in self._key_freq:
            self.on_access(key)
            return
        self._key_freq[key] = 1
        self._freq_keys.setdefault(1, OrderedDict())[key] = None
        self._min_freq = 1

    def on_access(self, key: str) -> None:
        freq = self._key_freq.get(key)
        if freq is None:
            return
        bucket = self._freq_keys[freq]
        del bucket[key]
        if not bucket:
            del self._freq_keys[freq]
            if self._min_freq == freq:
                self._min_freq = freq + 1
        new_freq = freq + 1
        self._key_freq[key] = new_freq
        self._freq_keys.setdefault(new_freq, OrderedDict())[key] = None

    def on_remove(self, key: str) -> None:
        freq = self._key_freq.pop(key, None)
        if freq is None:
            return
        bucket = self._freq_keys.get(freq)
        if bucket is not None:
            bucket.pop(key, None)
            if not bucket:
                del self._freq_keys[freq]
                if self._min_freq == freq:
                    self._min_freq = min(self._freq_keys) if self._freq_keys else 0

    def evict(self) -> str:
        if not self._key_freq:
            raise CacheEmptyError("nothing to evict")
        bucket = self._freq_keys[self._min_freq]
        key, _ = bucket.popitem(last=False)  # oldest at lowest freq
        del self._key_freq[key]
        if not bucket:
            del self._freq_keys[self._min_freq]
            self._min_freq = min(self._freq_keys) if self._freq_keys else 0
        return key

    def frequency_of(self, key: str) -> int:
        return self._key_freq.get(key, 0)

    def clear(self) -> None:
        self._key_freq.clear()
        self._freq_keys.clear()
        self._min_freq = 0

    def __len__(self) -> int:
        return len(self._key_freq)

    def __contains__(self, key: str) -> bool:
        return key in self._key_freq
