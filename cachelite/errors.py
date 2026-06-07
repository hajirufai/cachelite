"""Custom exceptions for CacheLite."""


class CacheError(Exception):
    """Base class for all CacheLite errors."""


class CacheEmptyError(CacheError):
    """Raised when an eviction is requested but the cache is empty."""


class CacheKeyError(CacheError):
    """Raised when a key is invalid (wrong type, empty, etc.)."""


class CacheFullError(CacheError):
    """Raised when a value cannot be stored even after eviction.

    This happens when a single value is larger than the cache's max_bytes
    budget, so no amount of eviction can make room for it.
    """


class UnknownPolicyError(CacheError):
    """Raised when an unknown eviction policy name is requested."""


class SnapshotError(CacheError):
    """Raised when a snapshot fails to save or load (corruption, bad format)."""
