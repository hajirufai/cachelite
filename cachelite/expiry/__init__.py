"""Expiry strategies: lazy (inline) + active (background sweeper)."""

from .active import ActiveExpiry
from .lazy import is_expired
from .ttl import deadline_from_ttl, ttl_from_deadline

__all__ = ["ActiveExpiry", "is_expired", "deadline_from_ttl", "ttl_from_deadline"]
