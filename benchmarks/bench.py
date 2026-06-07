"""Micro-benchmarks for CacheLite — throughput for set/get and each policy.

Run: python benchmarks/bench.py
These are rough, single-machine numbers meant to show relative behaviour,
not absolute performance claims.
"""

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cachelite import Cache  # noqa: E402


def bench_set(n=100_000):
    cache = Cache(max_items=n)
    start = time.perf_counter()
    for i in range(n):
        cache.set(f"key:{i}", i)
    elapsed = time.perf_counter() - start
    print(f"set    : {n:,} ops in {elapsed:.3f}s -> {n / elapsed:,.0f} ops/s")


def bench_get(n=100_000):
    cache = Cache(max_items=n)
    for i in range(n):
        cache.set(f"key:{i}", i)
    keys = [f"key:{random.randrange(n)}" for _ in range(n)]
    start = time.perf_counter()
    for k in keys:
        cache.get(k)
    elapsed = time.perf_counter() - start
    print(f"get    : {n:,} ops in {elapsed:.3f}s -> {n / elapsed:,.0f} ops/s")


def bench_eviction(policy, n=100_000, cap=10_000):
    cache = Cache(max_items=cap, policy=policy)
    start = time.perf_counter()
    for i in range(n):
        cache.set(f"key:{i}", i)
    elapsed = time.perf_counter() - start
    evicted = cache.stats().evictions
    print(f"{policy:<7}: {n:,} inserts, {evicted:,} evictions in "
          f"{elapsed:.3f}s -> {n / elapsed:,.0f} ops/s")


def main():
    print("CacheLite benchmarks (stdlib only)\n" + "-" * 42)
    bench_set()
    bench_get()
    print("\nEviction throughput (cap=10k, 100k inserts):")
    for policy in ["lru", "lfu", "fifo", "random"]:
        bench_eviction(policy)


if __name__ == "__main__":
    main()
