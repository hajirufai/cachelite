import time
import unittest

from cachelite import Cache
from cachelite.expiry.ttl import deadline_from_ttl, ttl_from_deadline


class TestTTL(unittest.TestCase):
    def test_expiry_on_get(self):
        c = Cache(max_items=10)
        c.set("a", 1, ttl=0.2)
        self.assertEqual(c.get("a"), 1)
        time.sleep(0.25)
        self.assertIsNone(c.get("a"))

    def test_expiration_counted(self):
        c = Cache(max_items=10)
        c.set("a", 1, ttl=0.1)
        time.sleep(0.15)
        c.get("a")
        self.assertEqual(c.stats().expirations, 1)

    def test_has_respects_expiry(self):
        c = Cache(max_items=10)
        c.set("a", 1, ttl=0.1)
        time.sleep(0.15)
        self.assertFalse(c.has("a"))

    def test_ttl_query(self):
        c = Cache(max_items=10)
        c.set("a", 1, ttl=10)
        remaining = c.ttl("a")
        self.assertTrue(0 < remaining <= 10)
        c.set("b", 2)
        self.assertIsNone(c.ttl("b"))
        self.assertIsNone(c.ttl("missing"))

    def test_touch_resets_ttl(self):
        c = Cache(max_items=10)
        c.set("a", 1, ttl=0.2)
        time.sleep(0.1)
        self.assertTrue(c.touch("a", ttl=10))
        self.assertGreater(c.ttl("a"), 1)
        self.assertFalse(c.touch("missing"))

    def test_expire_method(self):
        c = Cache(max_items=10)
        c.set("a", 1)
        self.assertTrue(c.expire("a", 0.1))
        time.sleep(0.15)
        self.assertIsNone(c.get("a"))

    def test_persist_removes_ttl(self):
        c = Cache(max_items=10)
        c.set("a", 1, ttl=0.2)
        self.assertTrue(c.persist("a"))
        time.sleep(0.25)
        self.assertEqual(c.get("a"), 1)

    def test_default_ttl(self):
        c = Cache(max_items=10, default_ttl=0.1)
        c.set("a", 1)  # no explicit ttl -> uses default
        time.sleep(0.15)
        self.assertIsNone(c.get("a"))

    def test_size_purges_expired(self):
        c = Cache(max_items=10)
        c.set("a", 1, ttl=0.1)
        c.set("b", 2)
        time.sleep(0.15)
        self.assertEqual(c.size(), 1)


class TestTTLHelpers(unittest.TestCase):
    def test_deadline_roundtrip(self):
        d = deadline_from_ttl(10)
        self.assertTrue(9 < ttl_from_deadline(d) <= 10)

    def test_none_ttl(self):
        self.assertIsNone(deadline_from_ttl(None))
        self.assertIsNone(deadline_from_ttl(0))
        self.assertIsNone(ttl_from_deadline(None))

    def test_negative_ttl_raises(self):
        with self.assertRaises(ValueError):
            deadline_from_ttl(-1)

    def test_past_deadline_clamped_to_zero(self):
        self.assertEqual(ttl_from_deadline(0, now=100), 0.0)


if __name__ == "__main__":
    unittest.main()
