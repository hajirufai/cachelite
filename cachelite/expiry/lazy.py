"""Lazy expiry helpers.

Lazy expiry is the default and is handled inline by the Cache: every get()/
has() checks ``entry.is_expired()`` and removes the key on the spot. This
module exposes the predicate so the strategy is documented and testable on
its own, and so other components can reuse the exact same check.
"""

from __future__ import annotations

from typing import Optional

from ..types import CacheEntry


def is_expired(entry: CacheEntry, now: Optional[float] = None) -> bool:
    """Return True if the entry has passed its TTL deadline."""
    return entry.is_expired(now)
