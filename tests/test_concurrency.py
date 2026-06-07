import threading
import unittest

from cachelite import Cache


class TestConcurrency(unittest.TestCase):
    def test_concurrent_writes_no_corruption(self):
        c = Cache(max_items=10000)
        n_threads = 8
        per_thread = 500

        def writer(tid):
            for i in range(per_thread):
                c.set(f"t{tid}:k{i}", i)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
            self.assertFalse(t.is_alive())
        self.assertEqual(c.size(), n_threads * per_thread)

    def test_concurrent_read_write(self):
        c = Cache(max_items=10000)
        for i in range(100):
            c.set(f"k{i}", i)
        errors = []

        def reader():
            try:
                for _ in range(1000):
                    c.get(f"k{_ % 100}")
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        def writer():
            try:
                for i in range(1000):
                    c.set(f"k{i % 100}", i)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(4)]
        threads += [threading.Thread(target=writer) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        self.assertEqual(errors, [])

    def test_concurrent_eviction_keeps_capacity(self):
        c = Cache(max_items=100)

        def writer(tid):
            for i in range(500):
                c.set(f"t{tid}:k{i}", i)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        # capacity invariant must hold despite concurrent eviction races
        self.assertLessEqual(c.size(), 100)

    def test_stats_consistency_under_load(self):
        c = Cache(max_items=10000)

        def worker():
            for i in range(200):
                c.set(f"k{i}", i)
                c.get(f"k{i}")

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        s = c.stats()
        # every get hit (set immediately before), 5*200 = 1000 hits
        self.assertEqual(s.hits, 1000)


if __name__ == "__main__":
    unittest.main()
