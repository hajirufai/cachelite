"""TTL caching: cache API-style responses that expire after a few seconds."""

import time

from cachelite import Cache


def fetch_exchange_rate(pair: str) -> float:
    """Pretend this hits a slow external FX API."""
    print(f"  [API] fetching live rate for {pair} ...")
    time.sleep(0.3)
    return {"USD/KES": 129.4, "EUR/KES": 141.2}[pair]


def main():
    cache = Cache(max_items=100, default_ttl=2)  # rates valid for 2 seconds

    def get_rate(pair: str) -> float:
        cached = cache.get(pair)
        if cached is not None:
            print(f"  [cache] hit for {pair}")
            return cached
        rate = fetch_exchange_rate(pair)
        cache.set(pair, rate)
        return rate

    print("First lookups (cold cache):")
    print("  USD/KES =", get_rate("USD/KES"))
    print("  USD/KES =", get_rate("USD/KES"))  # served from cache

    print(f"\n  remaining ttl: {cache.ttl('USD/KES'):.2f}s")
    print("\nWaiting for the cached rate to expire...")
    time.sleep(2.1)
    print("  USD/KES =", get_rate("USD/KES"))  # re-fetched


if __name__ == "__main__":
    main()
