"""Pattern invalidation: bulk-delete keys by glob, like Redis KEYS/DEL."""

from cachelite import Cache


def main():
    cache = Cache(max_items=1000)

    # Populate a namespaced keyspace.
    for uid in range(3):
        cache.set(f"user:{uid}:profile", {"id": uid})
        cache.set(f"user:{uid}:settings", {"theme": "dark"})
    cache.set("config:global", {"region": "nairobi"})

    print("all keys:", sorted(cache.keys()))
    print("user:1 keys:", sorted(cache.keys("user:1:*")))

    # User 1 logs out — drop everything under their namespace in one call.
    removed = cache.invalidate("user:1:*")
    print(f"\ninvalidated {removed} keys for user:1")
    print("remaining keys:", sorted(cache.keys()))

    # config and other users are untouched.
    print("config still present?", cache.has("config:global"))


if __name__ == "__main__":
    main()
