import unittest

from cachelite.errors import CacheEmptyError
from cachelite.eviction.lru import LRUPolicy


class TestLRUPolicy(unittest.TestCase):
    def setUp(self):
        self.p = LRUPolicy()

    def test_evict_order_is_least_recently_used(self):
        for k in ["a", "b", "c"]:
            self.p.on_insert(k)
        self.assertEqual(self.p.evict(), "a")
        self.assertEqual(self.p.evict(), "b")

    def test_access_promotes_to_mru(self):
        for k in ["a", "b", "c"]:
            self.p.on_insert(k)
        self.p.on_access("a")  # a becomes MRU, b is now LRU
        self.assertEqual(self.p.evict(), "b")

    def test_reinsert_existing_promotes(self):
        for k in ["a", "b", "c"]:
            self.p.on_insert(k)
        self.p.on_insert("a")  # should promote, not duplicate
        self.assertEqual(len(self.p), 3)
        self.assertEqual(self.p.evict(), "b")

    def test_remove_then_evict(self):
        for k in ["a", "b", "c"]:
            self.p.on_insert(k)
        self.p.on_remove("a")
        self.assertNotIn("a", self.p)
        self.assertEqual(self.p.evict(), "b")

    def test_remove_missing_is_noop(self):
        self.p.on_insert("a")
        self.p.on_remove("zzz")  # should not raise
        self.assertEqual(len(self.p), 1)

    def test_evict_empty_raises(self):
        with self.assertRaises(CacheEmptyError):
            self.p.evict()

    def test_access_missing_is_noop(self):
        self.p.on_access("ghost")  # no crash
        self.assertEqual(len(self.p), 0)

    def test_clear(self):
        for k in ["a", "b"]:
            self.p.on_insert(k)
        self.p.clear()
        self.assertEqual(len(self.p), 0)
        with self.assertRaises(CacheEmptyError):
            self.p.evict()

    def test_contains(self):
        self.p.on_insert("x")
        self.assertIn("x", self.p)
        self.assertNotIn("y", self.p)

    def test_large_sequence_consistency(self):
        for i in range(1000):
            self.p.on_insert(f"k{i}")
        # access even keys to keep them
        for i in range(0, 1000, 2):
            self.p.on_access(f"k{i}")
        # first evicted should be an odd key (never accessed, oldest)
        self.assertEqual(self.p.evict(), "k1")


if __name__ == "__main__":
    unittest.main()
