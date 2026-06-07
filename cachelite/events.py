"""Event system — pluggable callbacks for cache lifecycle events.

Handlers are isolated: if one raises, the others still run and the exception
is swallowed (optionally routed to a logger). A cache should never crash
because a metrics callback threw.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger("cachelite.events")

# Recognised event names.
ON_HIT = "hit"
ON_MISS = "miss"
ON_SET = "set"
ON_EVICT = "evict"
ON_EXPIRE = "expire"
ON_DELETE = "delete"
ON_CLEAR = "clear"

_VALID_EVENTS = {ON_HIT, ON_MISS, ON_SET, ON_EVICT, ON_EXPIRE, ON_DELETE, ON_CLEAR}


class CacheEvents:
    def __init__(self, suppress_errors: bool = True) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._suppress = suppress_errors

    def on(self, event: str, handler: Callable) -> Callable:
        """Register ``handler`` for ``event``. Returns the handler (decorator-friendly)."""
        if event not in _VALID_EVENTS:
            raise ValueError(f"unknown event {event!r}; valid: {sorted(_VALID_EVENTS)}")
        self._handlers[event].append(handler)
        return handler

    def off(self, event: str, handler: Callable) -> bool:
        """Unregister a handler. Returns True if it was found."""
        handlers = self._handlers.get(event, [])
        if handler in handlers:
            handlers.remove(handler)
            return True
        return False

    def emit(self, event: str, key: str, value: Any = None) -> None:
        for handler in self._handlers.get(event, ()):
            try:
                handler(key, value)
            except Exception:  # noqa: BLE001 - isolation is intentional
                if self._suppress:
                    logger.exception("event handler for %s failed", event)
                else:
                    raise

    def clear_handlers(self) -> None:
        self._handlers.clear()

    def handler_count(self, event: str | None = None) -> int:
        if event is None:
            return sum(len(h) for h in self._handlers.values())
        return len(self._handlers.get(event, []))
