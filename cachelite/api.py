"""A small RESTful HTTP API over a Cache, built on stdlib http.server.

Endpoints::

    GET    /health                 -> {"status": "ok"}
    GET    /stats                  -> cache statistics
    GET    /keys?pattern=user:*    -> {"keys": [...], "count": n}
    GET    /cache/<key>            -> {"key", "value", "ttl"} or 404
    PUT    /cache/<key>            -> body {"value": ..., "ttl": ...}; stores
    DELETE /cache/<key>            -> {"deleted": bool}
    POST   /flush                  -> {"cleared": n}
    POST   /invalidate             -> body {"pattern": "user:*"}; bulk delete

Responses are JSON. This is intentionally minimal — no auth, meant for a
trusted local network or as an embeddable admin surface.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .core.cache import Cache
from .errors import CacheError


def _make_handler(cache: Cache):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):  # silence default stderr logging
            pass

        # -- helpers ----------------------------------------------------
        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            if not length:
                return {}
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                return {}

        def _key_from_path(self, path: str) -> str | None:
            if path.startswith("/cache/"):
                return path[len("/cache/"):]
            return None

        # -- verbs ------------------------------------------------------
        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/health":
                return self._send(200, {"status": "ok"})
            if path == "/stats":
                return self._send(200, cache.stats().as_dict())
            if path == "/keys":
                qs = parse_qs(parsed.query)
                pattern = qs.get("pattern", [None])[0]
                keys = cache.keys(pattern)
                return self._send(200, {"keys": keys, "count": len(keys)})
            key = self._key_from_path(path)
            if key:
                if not cache.has(key):
                    return self._send(404, {"error": "not found", "key": key})
                return self._send(200, {
                    "key": key,
                    "value": cache.get(key),
                    "ttl": cache.ttl(key),
                })
            return self._send(404, {"error": "unknown route", "path": path})

        def do_PUT(self):
            key = self._key_from_path(urlparse(self.path).path)
            if not key:
                return self._send(404, {"error": "unknown route"})
            data = self._read_json()
            if "value" not in data:
                return self._send(400, {"error": "missing 'value'"})
            try:
                cache.set(key, data["value"], ttl=data.get("ttl"))
            except CacheError as exc:
                return self._send(400, {"error": str(exc)})
            return self._send(200, {"key": key, "stored": True})

        def do_DELETE(self):
            key = self._key_from_path(urlparse(self.path).path)
            if not key:
                return self._send(404, {"error": "unknown route"})
            return self._send(200, {"deleted": cache.delete(key)})

        def do_POST(self):
            path = urlparse(self.path).path
            if path == "/flush":
                return self._send(200, {"cleared": cache.clear()})
            if path == "/invalidate":
                data = self._read_json()
                pattern = data.get("pattern")
                if not pattern:
                    return self._send(400, {"error": "missing 'pattern'"})
                return self._send(200, {"invalidated": cache.invalidate(pattern)})
            return self._send(404, {"error": "unknown route", "path": path})

    return Handler


class CacheServer:
    """Threaded HTTP server wrapping a Cache."""

    def __init__(self, cache: Cache, host: str = "127.0.0.1", port: int = 8080) -> None:
        self.cache = cache
        self.host = host
        self.port = port
        self._httpd = ThreadingHTTPServer((host, port), _make_handler(cache))
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        return self._httpd.server_address

    def serve_forever(self) -> None:
        self._httpd.serve_forever()

    def start_background(self) -> None:
        self._thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._thread.start()

    def shutdown(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2.0)


def serve(cache: Cache | None = None, host: str = "127.0.0.1", port: int = 8080) -> None:
    cache = cache or Cache(max_items=10000)
    server = CacheServer(cache, host, port)
    print(f"CacheLite API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.shutdown()
