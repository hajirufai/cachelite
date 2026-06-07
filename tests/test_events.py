import unittest

from cachelite import Cache
from cachelite.events import (CacheEvents, ON_EVICT, ON_HIT, ON_MISS, ON_SET)


class TestEvents(unittest.TestCase):
    def test_hit_and_miss_events(self):
        c = Cache(max_items=10)
        log = []
        c.events.on(ON_HIT, lambda k, v: log.append(("hit", k)))
        c.events.on(ON_MISS, lambda k, v: log.append(("miss", k)))
        c.set("a", 1)
        c.get("a")
        c.get("b")
        self.assertIn(("hit", "a"), log)
        self.assertIn(("miss", "b"), log)

    def test_set_event(self):
        c = Cache(max_items=10)
        seen = []
        c.events.on(ON_SET, lambda k, v: seen.append((k, v)))
        c.set("x", 42)
        self.assertEqual(seen, [("x", 42)])

    def test_evict_event(self):
        c = Cache(max_items=2)
        evicted = []
        c.events.on(ON_EVICT, lambda k, v: evicted.append(k))
        for i in range(4):
            c.set(f"k{i}", i)
        self.assertEqual(len(evicted), 2)

    def test_unknown_event_raises(self):
        ev = CacheEvents()
        with self.assertRaises(ValueError):
            ev.on("nonsense", lambda k, v: None)

    def test_handler_isolation(self):
        ev = CacheEvents(suppress_errors=True)
        ok = []

        def bad(k, v):
            raise RuntimeError("boom")

        def good(k, v):
            ok.append(k)

        ev.on(ON_HIT, bad)
        ev.on(ON_HIT, good)
        ev.emit(ON_HIT, "k")  # bad raises but is swallowed
        self.assertEqual(ok, ["k"])

    def test_handler_error_propagates_when_not_suppressed(self):
        ev = CacheEvents(suppress_errors=False)
        ev.on(ON_HIT, lambda k, v: (_ for _ in ()).throw(RuntimeError("x")))
        with self.assertRaises(RuntimeError):
            ev.emit(ON_HIT, "k")

    def test_off_unregisters(self):
        ev = CacheEvents()
        h = lambda k, v: None
        ev.on(ON_HIT, h)
        self.assertTrue(ev.off(ON_HIT, h))
        self.assertFalse(ev.off(ON_HIT, h))

    def test_handler_count(self):
        ev = CacheEvents()
        ev.on(ON_HIT, lambda k, v: None)
        ev.on(ON_MISS, lambda k, v: None)
        self.assertEqual(ev.handler_count(), 2)
        self.assertEqual(ev.handler_count(ON_HIT), 1)

    def test_clear_handlers(self):
        ev = CacheEvents()
        ev.on(ON_HIT, lambda k, v: None)
        ev.clear_handlers()
        self.assertEqual(ev.handler_count(), 0)


if __name__ == "__main__":
    unittest.main()
