"""The @cached decorator — memoize function results through a Cache."""

from __future__ import annotations

import functools
import hashlib
from typing import Any, Callable, Optional

_MISS = object()


def _default_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """Build a stable cache key from the call signature.

    We hash the repr of args/kwargs so even large or unhashable-but-reprable
    arguments produce a short, deterministic key. kwargs are sorted so call
    order doesn't matter.
    """
    raw = f"{func.__module__}.{func.__qualname__}|{args!r}|{sorted(kwargs.items())!r}"
    digest = hashlib.blake2b(raw.encode("utf-8"), digest_size=16).hexdigest()
    return f"{func.__qualname__}:{digest}"


def cached(cache, ttl: Optional[float] = None,
           key_fn: Optional[Callable[..., str]] = None) -> Callable:
    """Decorator that memoizes a function's return value in ``cache``.

    Usage::

        cache = Cache(max_items=500)

        @cached(cache, ttl=30)
        def fib(n):
            return n if n < 2 else fib(n - 1) + fib(n - 2)

    The wrapper exposes ``.cache_clear()`` and ``.cache_info()``. A sentinel
    value distinguishes "stored None" from "cache miss", so caching a function
    that legitimately returns None still works.
    """

    def decorator(func: Callable) -> Callable:
        prefix = f"{func.__qualname__}:"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if key_fn is not None:
                key = key_fn(*args, **kwargs)
            else:
                key = _default_key(func, args, kwargs)
            found = cache.get(key, _MISS)
            if found is not _MISS:
                return found
            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            return result

        wrapper.cache_clear = lambda: cache.invalidate(f"{prefix}*")  # type: ignore[attr-defined]
        wrapper.cache_info = lambda: cache.stats()  # type: ignore[attr-defined]
        wrapper.__wrapped__ = func  # type: ignore[attr-defined]
        return wrapper

    return decorator
