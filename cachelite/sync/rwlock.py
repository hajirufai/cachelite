"""A reader-writer lock: many concurrent readers OR one exclusive writer."""

from __future__ import annotations

import threading
from contextlib import contextmanager


class ReadWriteLock:
    """Writer-blocking RWLock.

    The first reader acquires the writer lock; the last reader releases it.
    While any reader holds the lock, writers wait. This favors readers, which
    matches a cache's typical read-heavy workload.

    Note: this implementation can starve writers under sustained read load.
    That's an acceptable trade-off for a read-dominated cache, and it keeps
    the lock simple and fast.
    """

    def __init__(self) -> None:
        self._readers = 0
        self._readers_lock = threading.Lock()
        self._writer_lock = threading.Lock()

    def read_acquire(self) -> None:
        with self._readers_lock:
            self._readers += 1
            if self._readers == 1:
                self._writer_lock.acquire()

    def read_release(self) -> None:
        with self._readers_lock:
            if self._readers == 0:
                raise RuntimeError("read_release without matching acquire")
            self._readers -= 1
            if self._readers == 0:
                self._writer_lock.release()

    def write_acquire(self) -> None:
        self._writer_lock.acquire()

    def write_release(self) -> None:
        self._writer_lock.release()

    @contextmanager
    def read(self):
        self.read_acquire()
        try:
            yield
        finally:
            self.read_release()

    @contextmanager
    def write(self):
        self.write_acquire()
        try:
            yield
        finally:
            self.write_release()
