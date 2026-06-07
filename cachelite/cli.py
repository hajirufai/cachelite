"""Command-line interface for CacheLite.

Because the cache lives in-process, a long-lived store needs the ``serve``
command (HTTP API) or snapshots to persist across invocations. The one-shot
commands (set/get/...) operate on a snapshot file passed via ``--store``,
loading it, applying the operation, and saving it back — a simple file-backed
key/value tool you can script from a shell.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .api import serve
from .core.cache import Cache
from .errors import CacheError
from .utils import human_bytes, human_duration


def _load(store_path: str, policy: str, max_items: int) -> Cache:
    cache = Cache(max_items=max_items, policy=policy)
    if store_path and os.path.exists(store_path):
        cache.restore(store_path)
    return cache


def _save(cache: Cache, store_path: str) -> None:
    if store_path:
        cache.snapshot(store_path, fmt="json")


def _parse_value(raw: str):
    """Try to parse the value as JSON, falling back to a plain string."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def cmd_set(args) -> int:
    cache = _load(args.store, args.policy, args.max_items)
    try:
        cache.set(args.key, _parse_value(args.value), ttl=args.ttl)
    except CacheError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _save(cache, args.store)
    print(f"OK set {args.key}")
    return 0


def cmd_get(args) -> int:
    cache = _load(args.store, args.policy, args.max_items)
    value = cache.get(args.key, _MISSING)
    if value is _MISSING:
        print(f"(nil) {args.key} not found", file=sys.stderr)
        return 1
    print(json.dumps(value))
    return 0


def cmd_delete(args) -> int:
    cache = _load(args.store, args.policy, args.max_items)
    ok = cache.delete(args.key)
    _save(cache, args.store)
    print("deleted" if ok else "(nil) not found")
    return 0 if ok else 1


def cmd_keys(args) -> int:
    cache = _load(args.store, args.policy, args.max_items)
    for key in sorted(cache.keys(args.pattern)):
        print(key)
    return 0


def cmd_flush(args) -> int:
    cache = _load(args.store, args.policy, args.max_items)
    n = cache.clear()
    _save(cache, args.store)
    print(f"cleared {n} entries")
    return 0


def cmd_stats(args) -> int:
    cache = _load(args.store, args.policy, args.max_items)
    s = cache.stats()
    print(f"items       : {s.current_items}")
    print(f"memory      : {human_bytes(s.current_bytes)}")
    print(f"hits/misses : {s.hits}/{s.misses}  (hit rate {s.hit_rate:.1%})")
    print(f"evictions   : {s.evictions}")
    print(f"expirations : {s.expirations}")
    print(f"uptime      : {human_duration(s.uptime_seconds)}")
    return 0


def cmd_serve(args) -> int:
    cache = _load(args.store, args.policy, args.max_items)
    serve(cache, host=args.host, port=args.port)
    return 0


def cmd_demo(args) -> int:
    """Run a quick interactive demo of the cache's capabilities."""
    import time

    print("CacheLite demo — LRU cache, max 3 items\n")
    cache = Cache(max_items=3, policy="lru")
    for k, v in [("a", 1), ("b", 2), ("c", 3)]:
        cache.set(k, v)
        print(f"  set {k}={v}")
    print(f"  touch 'a' (read): {cache.get('a')}")
    cache.set("d", 4)
    print("  set d=4 -> evicts least-recently-used ('b')")
    print(f"  live keys: {sorted(cache.keys())}\n")

    print("TTL demo:")
    cache.set("temp", "gone soon", ttl=0.5)
    print(f"  temp now: {cache.get('temp')}  (ttl {cache.ttl('temp'):.2f}s)")
    time.sleep(0.6)
    print(f"  temp after 0.6s: {cache.get('temp')}\n")

    print(f"  stats: {json.dumps(cache.stats().as_dict(), indent=2)}")
    return 0


_MISSING = object()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cachelite", description="CacheLite cache engine")
    p.add_argument("--version", action="version", version=f"cachelite {__version__}")
    p.add_argument("--store", default=os.environ.get("CACHELITE_STORE", ""),
                   help="snapshot file for persistence between commands")
    p.add_argument("--policy", default="lru", choices=["lru", "lfu", "fifo", "random"])
    p.add_argument("--max-items", type=int, default=10000, dest="max_items")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("set", help="store a key")
    sp.add_argument("key"); sp.add_argument("value")
    sp.add_argument("--ttl", type=float, default=None)
    sp.set_defaults(func=cmd_set)

    sp = sub.add_parser("get", help="read a key")
    sp.add_argument("key"); sp.set_defaults(func=cmd_get)

    sp = sub.add_parser("delete", help="remove a key")
    sp.add_argument("key"); sp.set_defaults(func=cmd_delete)

    sp = sub.add_parser("keys", help="list keys, optional glob pattern")
    sp.add_argument("pattern", nargs="?", default=None)
    sp.set_defaults(func=cmd_keys)

    sub.add_parser("flush", help="remove all keys").set_defaults(func=cmd_flush)
    sub.add_parser("stats", help="show statistics").set_defaults(func=cmd_stats)
    sub.add_parser("demo", help="run an interactive demo").set_defaults(func=cmd_demo)

    sp = sub.add_parser("serve", help="start the HTTP API server")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8080)
    sp.set_defaults(func=cmd_serve)
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
