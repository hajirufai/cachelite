import unittest

from cachelite.core.config import CacheConfig
from cachelite.errors import CacheKeyError, UnknownPolicyError
from cachelite.eviction import make_policy
from cachelite.types import CacheEntry, EvictionPolicy
from cachelite.utils import (estimate_size, human_bytes, human_duration,
                             validate_key)


class TestUtils(unittest.TestCase):
    def test_validate_key(self):
        self.assertEqual(validate_key("abc"), "abc")
        with self.assertRaises(CacheKeyError):
            validate_key(123)
        with self.assertRaises(CacheKeyError):
            validate_key("")

    def test_estimate_size_deep(self):
        small = estimate_size("hi")
        big = estimate_size(["x" * 1000] * 10)
        self.assertGreater(big, small)

    def test_estimate_size_handles_cycles(self):
        a = []
        a.append(a)  # self-referential
        # must not infinite-loop
        self.assertGreater(estimate_size(a), 0)

    def test_estimate_size_nested_dict(self):
        d = {"a": {"b": {"c": [1, 2, 3]}}}
        self.assertGreater(estimate_size(d), 0)

    def test_human_bytes(self):
        self.assertEqual(human_bytes(512), "512 B")
        self.assertEqual(human_bytes(1536), "1.5 KB")
        self.assertIn("MB", human_bytes(5 * 1024 * 1024))

    def test_human_duration(self):
        self.assertEqual(human_duration(30), "30s")
        self.assertIn("m", human_duration(90))
        self.assertIn("h", human_duration(3700))


class TestConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = CacheConfig()
        self.assertEqual(cfg.policy, EvictionPolicy.LRU)

    def test_string_policy_coerced(self):
        cfg = CacheConfig(policy="lfu")
        self.assertEqual(cfg.policy, EvictionPolicy.LFU)

    def test_invalid_max_items(self):
        with self.assertRaises(ValueError):
            CacheConfig(max_items=0)

    def test_invalid_max_bytes(self):
        with self.assertRaises(ValueError):
            CacheConfig(max_bytes=-5)

    def test_both_none_raises(self):
        with self.assertRaises(ValueError):
            CacheConfig(max_items=None, max_bytes=None)

    def test_invalid_stripes(self):
        with self.assertRaises(ValueError):
            CacheConfig(num_stripes=0)

    def test_invalid_default_ttl(self):
        with self.assertRaises(ValueError):
            CacheConfig(default_ttl=-1)


class TestPolicyFactory(unittest.TestCase):
    def test_make_each_policy(self):
        for name in ["lru", "lfu", "fifo", "random"]:
            self.assertIsNotNone(make_policy(name))

    def test_make_from_enum(self):
        self.assertIsNotNone(make_policy(EvictionPolicy.LRU))

    def test_unknown_policy_raises(self):
        with self.assertRaises(UnknownPolicyError):
            make_policy("nonsense")


class TestCacheEntry(unittest.TestCase):
    def test_no_expiry(self):
        e = CacheEntry(key="k", value=1)
        self.assertFalse(e.is_expired())
        self.assertIsNone(e.remaining_ttl())

    def test_touch_increments_frequency(self):
        e = CacheEntry(key="k", value=1)
        e.touch()
        e.touch()
        self.assertEqual(e.frequency, 2)

    def test_expiry_with_deadline(self):
        e = CacheEntry(key="k", value=1, expires_at=100)
        self.assertTrue(e.is_expired(now=200))
        self.assertFalse(e.is_expired(now=50))

    def test_enum_from_string(self):
        self.assertEqual(EvictionPolicy.from_string("LRU"), EvictionPolicy.LRU)
        with self.assertRaises(ValueError):
            EvictionPolicy.from_string("bogus")


if __name__ == "__main__":
    unittest.main()
