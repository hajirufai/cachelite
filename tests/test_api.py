import json
import time
import unittest
import urllib.error
import urllib.request

from cachelite import Cache
from cachelite.api import CacheServer


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = Cache(max_items=100)
        cls.server = CacheServer(cls.cache, host="127.0.0.1", port=8077)
        cls.server.start_background()
        time.sleep(0.2)
        cls.base = "http://127.0.0.1:8077"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def _req(self, method, path, data=None):
        body = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(self.base + path, data=body, method=method)
        try:
            resp = urllib.request.urlopen(req)
            return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_health(self):
        code, body = self._req("GET", "/health")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "ok")

    def test_put_and_get(self):
        self._req("PUT", "/cache/foo", {"value": {"a": 1}})
        code, body = self._req("GET", "/cache/foo")
        self.assertEqual(code, 200)
        self.assertEqual(body["value"], {"a": 1})

    def test_get_missing_404(self):
        code, body = self._req("GET", "/cache/ghost")
        self.assertEqual(code, 404)

    def test_put_missing_value_400(self):
        code, body = self._req("PUT", "/cache/x", {"nope": 1})
        self.assertEqual(code, 400)

    def test_delete(self):
        self._req("PUT", "/cache/todelete", {"value": 1})
        code, body = self._req("DELETE", "/cache/todelete")
        self.assertEqual(code, 200)
        self.assertTrue(body["deleted"])

    def test_keys_with_pattern(self):
        self._req("PUT", "/cache/user:1", {"value": 1})
        self._req("PUT", "/cache/user:2", {"value": 2})
        code, body = self._req("GET", "/keys?pattern=user:*")
        self.assertEqual(code, 200)
        self.assertGreaterEqual(body["count"], 2)

    def test_invalidate(self):
        self._req("PUT", "/cache/sess:1", {"value": 1})
        self._req("PUT", "/cache/sess:2", {"value": 2})
        code, body = self._req("POST", "/invalidate", {"pattern": "sess:*"})
        self.assertEqual(code, 200)
        self.assertGreaterEqual(body["invalidated"], 2)

    def test_invalidate_missing_pattern_400(self):
        code, body = self._req("POST", "/invalidate", {})
        self.assertEqual(code, 400)

    def test_stats(self):
        code, body = self._req("GET", "/stats")
        self.assertEqual(code, 200)
        self.assertIn("hit_rate", body)

    def test_flush(self):
        self._req("PUT", "/cache/temp", {"value": 1})
        code, body = self._req("POST", "/flush")
        self.assertEqual(code, 200)
        self.assertIn("cleared", body)

    def test_unknown_route_404(self):
        code, body = self._req("GET", "/bogus")
        self.assertEqual(code, 404)

    def test_ttl_via_api(self):
        self._req("PUT", "/cache/withttl", {"value": 1, "ttl": 60})
        code, body = self._req("GET", "/cache/withttl")
        self.assertTrue(0 < body["ttl"] <= 60)


if __name__ == "__main__":
    unittest.main()
