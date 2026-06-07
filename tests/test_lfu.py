import unittest

from cachelite.errors import CacheEmptyError
from cachelite.eviction.lfu import LFUPolicy


class TestLFUPolicy(unittest.TestCase):
    def setUp(self):
        self.p = LFUPolicy()

    def test_evicts_least_frequent(self):
        for k in ["a", "b", "c"]:
            self.p.on_insert(k)
        self.p.on_access("a")
        self.p.on_access("a")
        self.p.on_access("b")
        # c has freq 1, lowest -> evicted first
        self.assertEqual(self.p.evict(), "c")

    def test_tie_break_oldest_first(self):
        for k in ["a", "b", "c"]:
            self.p.on_insert(k)  # all freq 1
        # a inserted first -> evicted first on tie
        self.assertEqual(self.p.evict(), "a")
        self.assertEqual(self.p.evict(), "b")

    def test_min_freq_updates_after_eviction(self):
        self.p.on_insert("a")
        self.p.on_insert("b")
        self.p.on_access("a")  # a freq 2, b freq 1
        self.assertEqual(self.p.evict(), "b")  # min was 1
        self.assertEqual(self.p.evict(), "a")  # now min is 2

    def test_frequency_tracking(self):
        self.p.on_insert("a")
        self.assertEqual(self.p.frequency_of("a"), 1)
        self.p.on_access("a")
        self.assertEqual(self.p.frequency_of("a"), 2)
        self.assertEqual(self.p.frequency_of("missing"), 0)

    def test_remove_updates_min_freq(self):
        self.p.on_insert("a")
        self.p.on_insert("b")
        self.p.on_access("a")  # a:2 b:1
        self.p.on_remove("b")  # min should recompute to 2
        self.assertEqual(self.p.evict(), "a")

    def test_reinsert_existing_increments(self):
        self.p.on_insert("a")
        self.p.on_insert("a")  # treated as access
        self.assertEqual(self.p.frequency_of("a"), 2)
        self.assertEqual(len(self.p), 1)

    def test_evict_empty_raises(self):
        with self.assertRaises(CacheEmptyError):
            self.p.evict()

    def test_clear(self):
        self.p.on_insert("a")
        self.p.clear()
        self.assertEqual(len(self.p), 0)

    def test_remove_missing_noop(self):
        self.p.on_insert("a")
        self.p.on_remove("ghost")
        self.assertEqual(len(self.p), 1)

    def test_access_missing_noop(self):
        self.p.on_access("ghost")
        self.assertEqual(len(self.p), 0)


if __name__ == "__main__":
    unittest.main()
