import unittest

from cachelite.errors import CacheEmptyError
from cachelite.eviction.fifo import FIFOPolicy


class TestFIFOPolicy(unittest.TestCase):
    def setUp(self):
        self.p = FIFOPolicy()

    def test_insertion_order_eviction(self):
        for k in ["a", "b", "c"]:
            self.p.on_insert(k)
        self.assertEqual(self.p.evict(), "a")
        self.assertEqual(self.p.evict(), "b")
        self.assertEqual(self.p.evict(), "c")

    def test_access_does_not_change_order(self):
        for k in ["a", "b", "c"]:
            self.p.on_insert(k)
        self.p.on_access("a")
        self.p.on_access("a")
        self.assertEqual(self.p.evict(), "a")  # still first in

    def test_remove_tombstones_then_skipped(self):
        for k in ["a", "b", "c"]:
            self.p.on_insert(k)
        self.p.on_remove("a")
        self.assertEqual(self.p.evict(), "b")  # a skipped

    def test_reinsert_keeps_position(self):
        for k in ["a", "b"]:
            self.p.on_insert(k)
        self.p.on_insert("a")  # no-op for position
        self.assertEqual(len(self.p), 2)
        self.assertEqual(self.p.evict(), "a")

    def test_evict_empty_raises(self):
        with self.assertRaises(CacheEmptyError):
            self.p.evict()

    def test_evict_all_tombstoned_raises(self):
        self.p.on_insert("a")
        self.p.on_remove("a")
        with self.assertRaises(CacheEmptyError):
            self.p.evict()

    def test_clear(self):
        self.p.on_insert("a")
        self.p.clear()
        self.assertEqual(len(self.p), 0)

    def test_contains(self):
        self.p.on_insert("a")
        self.assertIn("a", self.p)
        self.p.on_remove("a")
        self.assertNotIn("a", self.p)


if __name__ == "__main__":
    unittest.main()
