"""Snapshot persistence — save/load cache contents to disk (JSON or pickle).

TTLs are stored as *remaining seconds* (not absolute monotonic deadlines),
because monotonic timestamps are meaningless across process restarts. On
restore we rebuild the deadline relative to the new process clock.
"""

from __future__ import annotations

import json
import pickle
import time
from typing import Any, Iterable

from ..errors import SnapshotError
from ..types import CacheEntry

_MAGIC = "cachelite-snapshot"
_VERSION = 1


def _entry_to_record(entry: CacheEntry) -> dict:
    return {
        "key": entry.key,
        "value": entry.value,
        "size_bytes": entry.size_bytes,
        "frequency": entry.frequency,
        "ttl_remaining": entry.remaining_ttl(),  # None == no expiry
    }


def _record_to_entry(rec: dict) -> CacheEntry:
    ttl = rec.get("ttl_remaining")
    expires_at = (time.monotonic() + ttl) if ttl else None
    return CacheEntry(
        key=rec["key"],
        value=rec["value"],
        size_bytes=rec.get("size_bytes", 0),
        frequency=rec.get("frequency", 0),
        expires_at=expires_at,
    )


def save_snapshot(path: str, store: dict, config: Any, fmt: str = "json") -> int:
    records = [_entry_to_record(e) for e in store.values()]
    payload = {
        "magic": _MAGIC,
        "version": _VERSION,
        "policy": config.policy.value,
        "saved_at": time.time(),
        "count": len(records),
        "entries": records,
    }
    try:
        if fmt == "json":
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
        elif fmt == "pickle":
            with open(path, "wb") as fh:
                pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            raise SnapshotError(f"unknown snapshot format {fmt!r}")
    except (OSError, TypeError) as exc:
        raise SnapshotError(f"failed to save snapshot: {exc}") from exc
    return len(records)


def load_snapshot(path: str) -> list[CacheEntry]:
    try:
        # Sniff format: JSON snapshots start with '{'.
        with open(path, "rb") as fh:
            head = fh.read(1)
        if head == b"{":
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        else:
            with open(path, "rb") as fh:
                payload = pickle.load(fh)
    except FileNotFoundError as exc:
        raise SnapshotError(f"snapshot not found: {path}") from exc
    except (json.JSONDecodeError, pickle.UnpicklingError, EOFError) as exc:
        raise SnapshotError(f"corrupt snapshot: {exc}") from exc

    if not isinstance(payload, dict) or payload.get("magic") != _MAGIC:
        raise SnapshotError("not a valid CacheLite snapshot")
    return [_record_to_entry(rec) for rec in payload.get("entries", [])]
