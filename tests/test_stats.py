import unittest

from cachelite import Cache
from cachelite.stats import CacheStats, StatsCollector


class TestStats(unittest.TestCase):
    def test_hit_miss_tracking(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        c.get("a")  # hit
        c.get("b")  # miss
        s = c.stats()
        self.assertEqual(s.hits, 1)
        self.assertEqual(s.misses, 1)
        self.assertAlmostEqual(s.hit_rate, 0.5)

    def test_set_delete_counts(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        c.set("b", 2)
        c.delete("a")
        s = c.stats()
        self.assertEqual(s.sets, 2)
        self.assertEqual(s.deletes, 1)

    def test_rates_with_no_activity(self):
        s = CacheStats()
        self.assertEqual(s.hit_rate, 0.0)
        self.assertEqual(s.miss_rate, 0.0)
        self.assertEqual(s.eviction_rate, 0.0)

    def test_eviction_rate(self):
        c = Cache(max_items=2)
        for i in range(5):
            c.set(f"k{i}", i)
        s = c.stats()
        self.assertEqual(s.evictions, 3)
        self.assertAlmostEqual(s.eviction_rate, 3 / 5)

    def test_as_dict_includes_rates(self):
        s = CacheStats(hits=3, misses=1)
        d = s.as_dict()
        self.assertIn("hit_rate", d)
        self.assertEqual(d["hit_rate"], 0.75)

    def test_reset_stats(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        c.get("a")
        c.reset_stats()
        s = c.stats()
        self.assertEqual(s.hits, 0)
        self.assertEqual(s.sets, 0)

    def test_collector_snapshot(self):
        sc = StatsCollector()
        sc.record_hit()
        sc.record_hit()
        sc.record_miss()
        snap = sc.snapshot(current_items=5, current_bytes=100, max_items=10, max_bytes=0)
        self.assertEqual(snap.hits, 2)
        self.assertEqual(snap.current_items, 5)
        self.assertGreaterEqual(snap.uptime_seconds, 0)

    def test_current_bytes_tracked(self):
        c = Cache(max_items=10)
        c.set("a", "x" * 100)
        self.assertGreater(c.stats().current_bytes, 100)
        c.delete("a")
        self.assertEqual(c.stats().current_bytes, 0)


if __name__ == "__main__":
    unittest.main()
