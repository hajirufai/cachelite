import os
import tempfile
import time
import unittest

from cachelite import Cache, cached


class TestIntegration(unittest.TestCase):
    def test_full_lifecycle(self):
        # populate -> evict -> snapshot -> restore -> verify
        c = Cache(max_items=5, policy="lru")
        for i in range(10):
            c.set(f"item:{i}", {"id": i, "data": "x" * 10})
        self.assertEqual(c.size(), 5)  # evicted down to capacity

        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "state.json")
        saved = c.snapshot(path)
        self.assertEqual(saved, 5)

        restored = Cache(max_items=10, policy="lru")
        loaded = restored.restore(path)
        self.assertEqual(loaded, 5)
        self.assertEqual(set(restored.keys()), set(c.keys()))

    def test_memoization_workflow(self):
        c = Cache(max_items=100, policy="lfu")
        computed = []

        @cached(c, ttl=60)
        def expensive(n):
            computed.append(n)
            total = 0
            for i in range(n):
                total += i
            return total

        for _ in range(5):
            expensive(100)
            expensive(200)
        # only computed once per unique arg despite 5 loops
        self.assertEqual(sorted(set(computed)), [100, 200])
        self.assertEqual(c.stats().hits, 8)

    def test_session_cache_with_ttl_and_invalidation(self):
        c = Cache(max_items=1000, default_ttl=0.3)
        for uid in range(5):
            c.set(f"session:{uid}", {"user": uid})
        self.assertEqual(len(c.keys("session:*")), 5)
        # bulk logout
        self.assertEqual(c.invalidate("session:*"), 5)
        self.assertEqual(len(c.keys("session:*")), 0)

    def test_mixed_policy_behaviour_consistency(self):
        for policy in ["lru", "lfu", "fifo", "random"]:
            c = Cache(max_items=50, policy=policy)
            for i in range(200):
                c.set(f"k{i}", i)
            self.assertEqual(c.size(), 50, f"policy {policy} broke capacity")

    def test_event_driven_metrics_pipeline(self):
        c = Cache(max_items=10)
        metrics = {"hits": 0, "misses": 0, "evictions": 0}
        from cachelite.events import ON_EVICT, ON_HIT, ON_MISS

        c.events.on(ON_HIT, lambda k, v: metrics.__setitem__("hits", metrics["hits"] + 1))
        c.events.on(ON_MISS, lambda k, v: metrics.__setitem__("misses", metrics["misses"] + 1))
        c.events.on(ON_EVICT, lambda k, v: metrics.__setitem__("evictions", metrics["evictions"] + 1))

        for i in range(20):
            c.set(f"k{i}", i)
        c.get("k19")
        c.get("missing")

        self.assertEqual(metrics["hits"], 1)
        self.assertEqual(metrics["misses"], 1)
        self.assertEqual(metrics["evictions"], 10)


if __name__ == "__main__":
    unittest.main()
