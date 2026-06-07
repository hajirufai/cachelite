"""Memoization: speed up expensive recursive functions with @cached."""

import time

from cachelite import Cache, cached

cache = Cache(max_items=1000)


@cached(cache)
def fib(n: int) -> int:
    """Naive recursive Fibonacci — exponential without memoization."""
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def main():
    start = time.perf_counter()
    result = fib(35)
    elapsed = time.perf_counter() - start

    print(f"fib(35) = {result}")
    print(f"computed in {elapsed * 1000:.2f} ms (memoized)")
    print("cache info:", fib.cache_info().as_dict())

    # Without caching, fib(35) makes ~30 million calls. With @cached, each n is
    # computed once. Clear the cache to prove it recomputes on demand.
    fib.cache_clear()
    print("\nafter cache_clear, cache size:", cache.size())


if __name__ == "__main__":
    main()
