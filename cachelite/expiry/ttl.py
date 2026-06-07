"""TTL helpers — convert between relative TTL and absolute monotonic deadlines."""

from __future__ import annotations

import time
from typing import Optional


def deadline_from_ttl(ttl: Optional[float], now: Optional[float] = None) -> Optional[float]:
    """Turn a relative TTL (seconds from now) into a monotonic deadline."""
    if not ttl:
        return None
    if ttl < 0:
        raise ValueError("ttl must be non-negative")
    now = time.monotonic() if now is None else now
    return now + ttl


def ttl_from_deadline(deadline: Optional[float], now: Optional[float] = None) -> Optional[float]:
    """Turn a monotonic deadline back into remaining seconds (never negative)."""
    if deadline is None:
        return None
    now = time.monotonic() if now is None else now
    return max(0.0, deadline - now)
