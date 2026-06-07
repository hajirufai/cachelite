import time
import unittest

from cachelite import Cache
from cachelite.core.config import CacheConfig
from cachelite.expiry.active import ActiveExpiry


class TestActiveExpiry(unittest.TestCase):
    def test_background_sweep_removes_expired(self):
        cfg = CacheConfig(max_items=1000, active_expiry=True,
                          sweep_interval=0.05, sweep_sample=100)
        c = Cache(config=cfg)
        for i in range(50):
            c.set(f"k{i}", i, ttl=0.1)
        time.sleep(0.4)  # let several sweeps run
        # internal store should be drained without anyone calling get()
        self.assertEqual(len(c._store), 0)
        c.close()

    def test_manual_sweep_once(self):
        c = Cache(max_items=1000)
        for i in range(20):
            c.set(f"k{i}", i, ttl=0.05)
        time.sleep(0.1)
        sweeper = ActiveExpiry(c, sample_size=100)
        removed = sweeper.sweep_once()
        self.assertEqual(removed, 20)

    def test_sweeper_start_stop_idempotent(self):
        c = Cache(max_items=10)
        sweeper = ActiveExpiry(c, interval=0.05)
        sweeper.start()
        sweeper.start()  # second start is a no-op
        self.assertTrue(sweeper.running)
        sweeper.stop()
        self.assertFalse(sweeper.running)

    def test_sweep_empty_cache(self):
        c = Cache(max_items=10)
        sweeper = ActiveExpiry(c)
        self.assertEqual(sweeper.sweep_once(), 0)


if __name__ == "__main__":
    unittest.main()
