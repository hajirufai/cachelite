"""Striped locking — shard keys across N locks to cut contention."""

from __future__ import annotations

from contextlib import contextmanager

from .rwlock import ReadWriteLock


class StripedLock:
    """Partition the keyspace into ``num_stripes`` independent RWLocks.

    Two threads touching different keys usually hash to different stripes and
    proceed in parallel, instead of serializing on one global lock. A power-of
    -two stripe count lets us mask instead of modulo, but we keep ``%`` for
    clarity since it isn't the bottleneck.

    ``global_write()`` grabs *every* stripe (in a fixed order to avoid
    deadlock) for whole-cache operations like clear() or snapshot().
    """

    def __init__(self, num_stripes: int = 16) -> None:
        if num_stripes < 1:
            raise ValueError("num_stripes must be >= 1")
        self._num = num_stripes
        self._stripes = [ReadWriteLock() for _ in range(num_stripes)]

    def _stripe_for(self, key: str) -> ReadWriteLock:
        return self._stripes[hash(key) % self._num]

    @contextmanager
    def read(self, key: str):
        with self._stripe_for(key).read():
            yield

    @contextmanager
    def write(self, key: str):
        with self._stripe_for(key).write():
            yield

    @contextmanager
    def global_write(self):
        acquired = []
        try:
            for stripe in self._stripes:
                stripe.write_acquire()
                acquired.append(stripe)
            yield
        finally:
            for stripe in reversed(acquired):
                stripe.write_release()

    @property
    def num_stripes(self) -> int:
        return self._num
