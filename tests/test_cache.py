import unittest

from cachelite import Cache
from cachelite.errors import CacheFullError, CacheKeyError


class TestCacheBasics(unittest.TestCase):
    def test_set_get(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        self.assertEqual(c.get("a"), 1)

    def test_get_missing_returns_default(self):
        c = Cache(max_items=10)
        self.assertIsNone(c.get("nope"))
        self.assertEqual(c.get("nope", "default"), "default")

    def test_overwrite(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        c.set("a", 2)
        self.assertEqual(c.get("a"), 2)
        self.assertEqual(c.size(), 1)

    def test_delete(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        self.assertTrue(c.delete("a"))
        self.assertFalse(c.delete("a"))
        self.assertIsNone(c.get("a"))

    def test_has_contains(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        self.assertTrue(c.has("a"))
        self.assertIn("a", c)
        self.assertNotIn("b", c)

    def test_clear(self):
        c = Cache(max_items=10)
        for i in range(5):
            c.set(f"k{i}", i)
        self.assertEqual(c.clear(), 5)
        self.assertEqual(c.size(), 0)

    def test_keys_and_pattern(self):
        c = Cache(max_items=10)
        c.set("user:1", 1)
        c.set("user:2", 2)
        c.set("post:1", 3)
        self.assertEqual(sorted(c.keys("user:*")), ["user:1", "user:2"])
        self.assertEqual(len(c.keys()), 3)

    def test_invalidate_pattern(self):
        c = Cache(max_items=10)
        c.set("user:1", 1)
        c.set("user:2", 2)
        c.set("post:1", 3)
        self.assertEqual(c.invalidate("user:*"), 2)
        self.assertEqual(c.keys(), ["post:1"])

    def test_invalid_key_type(self):
        c = Cache(max_items=10)
        with self.assertRaises(CacheKeyError):
            c.set(123, "x")
        with self.assertRaises(CacheKeyError):
            c.set("", "x")

    def test_items_iteration(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        c.set("b", 2)
        self.assertEqual(dict(c.items()), {"a": 1, "b": 2})

    def test_iter(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        self.assertEqual(list(c), ["a"])

    def test_none_value_distinguished_from_miss(self):
        c = Cache(max_items=10)
        c.set("a", None)
        self.assertTrue(c.has("a"))
        sentinel = object()
        self.assertIsNone(c.get("a", sentinel))


class TestEvictionPolicies(unittest.TestCase):
    def test_lru_eviction(self):
        c = Cache(max_items=2, policy="lru")
        c.set("a", 1)
        c.set("b", 2)
        c.get("a")  # a recently used
        c.set("c", 3)  # evicts b
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.get("c"), 3)

    def test_fifo_eviction(self):
        c = Cache(max_items=2, policy="fifo")
        c.set("a", 1)
        c.set("b", 2)
        c.get("a")  # access ignored by fifo
        c.set("c", 3)  # evicts a (first in)
        self.assertIsNone(c.get("a"))

    def test_lfu_eviction(self):
        c = Cache(max_items=2, policy="lfu")
        c.set("a", 1)
        c.set("b", 2)
        c.get("a")
        c.get("a")
        c.set("c", 3)  # evicts b (less frequent)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 1)

    def test_random_eviction_respects_capacity(self):
        c = Cache(max_items=3, policy="random")
        for i in range(10):
            c.set(f"k{i}", i)
        self.assertEqual(c.size(), 3)

    def test_eviction_counter(self):
        c = Cache(max_items=2)
        for i in range(5):
            c.set(f"k{i}", i)
        self.assertEqual(c.stats().evictions, 3)


class TestByteBudget(unittest.TestCase):
    def test_max_bytes_enforced(self):
        c = Cache(max_items=1000, max_bytes=400, policy="lru")
        for i in range(50):
            c.set(f"k{i}", "x" * 50)
        self.assertLessEqual(c.stats().current_bytes, 400)

    def test_value_too_large_raises(self):
        c = Cache(max_items=1000, max_bytes=100)
        with self.assertRaises(CacheFullError):
            c.set("big", "x" * 1000)


if __name__ == "__main__":
    unittest.main()
