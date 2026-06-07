"""Persistent cache: snapshot to disk and restore on restart."""

import os
import tempfile

from cachelite import Cache


def main():
    path = os.path.join(tempfile.gettempdir(), "cachelite_demo.json")

    # --- "first run": populate and snapshot ---
    cache = Cache(max_items=1000, policy="lru")
    for i in range(5):
        cache.set(f"page:{i}", f"rendered html for page {i}", ttl=3600)
    saved = cache.snapshot(path)
    print(f"snapshotted {saved} entries to disk")

    # --- "restart": brand new cache, restore from disk ---
    fresh = Cache(max_items=1000, policy="lru")
    loaded = fresh.restore(path)
    print(f"restored {loaded} entries into a fresh cache")
    print("page:3 =", fresh.get("page:3"))
    print("ttl preserved:", round(fresh.ttl("page:3"), 1), "seconds remaining")

    os.remove(path)


if __name__ == "__main__":
    main()
