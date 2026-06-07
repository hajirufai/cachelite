"""Basic usage: store and retrieve values with LRU eviction."""

from cachelite import Cache


def main():
    # A cache that holds at most 3 items, evicting least-recently-used.
    cache = Cache(max_items=3, policy="lru")

    cache.set("name", "Ada Lovelace")
    cache.set("role", "Mathematician")
    cache.set("born", 1815)

    print("name:", cache.get("name"))
    print("born:", cache.get("born"))

    # Reading 'name' marks it recently used, so the next insert evicts 'role'.
    cache.get("name")
    cache.set("field", "Computing")

    print("\nAfter inserting a 4th item into a size-3 cache:")
    print("  live keys:", sorted(cache.keys()))
    print("  'role' evicted?", cache.get("role") is None)

    print("\nStats:", cache.stats().as_dict())


if __name__ == "__main__":
    main()
