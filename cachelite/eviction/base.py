"""Eviction policy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EvictionPolicy(ABC):
    """Abstract base for all eviction policies.

    A policy tracks *ordering metadata* about keys — never the values
    themselves. The Cache owns the values; the policy just answers the
    question "which key should I drop next?" in O(1).

    Lifecycle hooks:
        on_insert(key): a new key was added to the cache
        on_access(key): an existing key was read or updated
        on_remove(key): a key was deleted out of band (not via evict())
        evict()       : choose + return the victim key, removing it from
                        the policy's bookkeeping
    """

    @abstractmethod
    def on_insert(self, key: str) -> None:
        ...

    @abstractmethod
    def on_access(self, key: str) -> None:
        ...

    @abstractmethod
    def on_remove(self, key: str) -> None:
        ...

    @abstractmethod
    def evict(self) -> str:
        """Return the victim key. Raises CacheEmptyError if nothing to evict."""

    @abstractmethod
    def clear(self) -> None:
        ...

    @abstractmethod
    def __len__(self) -> int:
        ...

    def __contains__(self, key: str) -> bool:  # pragma: no cover - default
        return False
