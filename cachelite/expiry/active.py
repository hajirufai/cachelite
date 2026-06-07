"""Active expiry — a background daemon that proactively sweeps expired keys.

Modeled on Redis's adaptive expiry cycle: each pass samples a handful of
random keys, drops the expired ones, and — if more than a quarter of the
sample was expired — immediately sweeps again, since a high expired ratio
suggests many more are waiting. Otherwise it sleeps until the next interval.
"""

from __future__ import annotations

import threading


class ActiveExpiry:
    def __init__(self, cache, interval: float = 1.0, sample_size: int = 20,
                 aggressive_ratio: float = 0.25, max_passes: int = 16) -> None:
        self._cache = cache
        self._interval = interval
        self._sample_size = sample_size
        self._aggressive_ratio = aggressive_ratio
        self._max_passes = max_passes
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.total_expired = 0

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="cachelite-expiry", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop.wait(self._interval):
            self.sweep_once()

    def sweep_once(self) -> int:
        """Run one (possibly multi-pass) sweep. Returns total keys expired."""
        expired_here = 0
        for _ in range(self._max_passes):
            keys = self._cache._sample_keys(self._sample_size)
            if not keys:
                break
            removed = self._cache._sweep_expired(keys)
            expired_here += removed
            ratio = removed / len(keys)
            if ratio <= self._aggressive_ratio:
                break
        self.total_expired += expired_here
        return expired_here

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
