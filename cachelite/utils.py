"""Helper utilities: size estimation, key validation, time formatting."""

from __future__ import annotations

import sys
from typing import Any

from .errors import CacheKeyError


def validate_key(key: Any) -> str:
    """Ensure a key is a non-empty string. Returns the key unchanged."""
    if not isinstance(key, str):
        raise CacheKeyError(f"key must be a str, got {type(key).__name__}")
    if not key:
        raise CacheKeyError("key must not be empty")
    return key


def estimate_size(value: Any, _seen: "set[int] | None" = None) -> int:
    """Best-effort deep size of a value in bytes.

    ``sys.getsizeof`` only measures the top-level object, so a list of strings
    reports a tiny size. We recurse into common containers and track visited
    object ids to avoid double-counting shared references and infinite loops
    on cyclic structures.
    """
    if _seen is None:
        _seen = set()
    oid = id(value)
    if oid in _seen:
        return 0
    _seen.add(oid)

    size = sys.getsizeof(value)
    if isinstance(value, (str, bytes, bytearray, int, float, bool, type(None))):
        return size
    if isinstance(value, dict):
        for k, v in value.items():
            size += estimate_size(k, _seen) + estimate_size(v, _seen)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            size += estimate_size(item, _seen)
    return size


def human_bytes(n: int) -> str:
    """Render a byte count like '1.5 MB'."""
    step = 1024.0
    value = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < step:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= step
    return f"{value:.1f} PB"


def human_duration(seconds: float) -> str:
    """Render seconds like '2h 5m 3s'."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    parts = []
    for label, size in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        if seconds >= size:
            parts.append(f"{seconds // size}{label}")
            seconds %= size
    return " ".join(parts)
