import os
import tempfile
import time
import unittest

from cachelite import Cache
from cachelite.errors import SnapshotError


class TestSnapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _path(self, name):
        return os.path.join(self.tmp, name)

    def test_json_roundtrip(self):
        c = Cache(max_items=100)
        c.set("a", {"x": 1})
        c.set("b", [1, 2, 3])
        path = self._path("snap.json")
        self.assertEqual(c.snapshot(path), 2)

        c2 = Cache(max_items=100)
        self.assertEqual(c2.restore(path), 2)
        self.assertEqual(c2.get("a"), {"x": 1})
        self.assertEqual(c2.get("b"), [1, 2, 3])

    def test_pickle_roundtrip(self):
        c = Cache(max_items=100)
        c.set("t", (1, 2, 3))  # tuple survives pickle, not json
        path = self._path("snap.pkl")
        c.snapshot(path, fmt="pickle")
        c2 = Cache(max_items=100)
        c2.restore(path)
        self.assertEqual(c2.get("t"), (1, 2, 3))

    def test_ttl_preserved_as_remaining(self):
        c = Cache(max_items=100)
        c.set("a", 1, ttl=10)
        path = self._path("ttl.json")
        c.snapshot(path)
        c2 = Cache(max_items=100)
        c2.restore(path)
        self.assertTrue(0 < c2.ttl("a") <= 10)

    def test_expired_keys_not_restored(self):
        c = Cache(max_items=100)
        c.set("a", 1, ttl=0.1)
        c.set("b", 2)
        time.sleep(0.15)
        path = self._path("exp.json")
        c.snapshot(path)  # snapshot purges expired first
        c2 = Cache(max_items=100)
        count = c2.restore(path)
        self.assertEqual(count, 1)
        self.assertIsNone(c2.get("a"))

    def test_missing_file_raises(self):
        c = Cache(max_items=10)
        with self.assertRaises(SnapshotError):
            c.restore(self._path("nope.json"))

    def test_corrupt_file_raises(self):
        path = self._path("bad.json")
        with open(path, "w") as fh:
            fh.write("{not valid json")
        c = Cache(max_items=10)
        with self.assertRaises(SnapshotError):
            c.restore(path)

    def test_non_snapshot_file_raises(self):
        path = self._path("other.json")
        with open(path, "w") as fh:
            fh.write('{"hello": "world"}')
        c = Cache(max_items=10)
        with self.assertRaises(SnapshotError):
            c.restore(path)


if __name__ == "__main__":
    unittest.main()
