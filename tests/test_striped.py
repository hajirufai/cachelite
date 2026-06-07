import threading
import unittest

from cachelite.sync.striped import StripedLock


class TestStripedLock(unittest.TestCase):
    def test_invalid_stripe_count(self):
        with self.assertRaises(ValueError):
            StripedLock(0)

    def test_same_key_same_stripe(self):
        sl = StripedLock(16)
        s1 = sl._stripe_for("hello")
        s2 = sl._stripe_for("hello")
        self.assertIs(s1, s2)

    def test_read_write_context_managers(self):
        sl = StripedLock(4)
        with sl.write("k"):
            pass
        with sl.read("k"):
            pass

    def test_global_write_acquires_all(self):
        sl = StripedLock(4)
        with sl.global_write():
            # all stripe writer locks are held; trying to acquire one would
            # block, so we just assert we got here without deadlock
            pass
        # after release we can use stripes again
        with sl.write("x"):
            pass

    def test_concurrent_different_keys_progress(self):
        sl = StripedLock(16)
        results = []

        def work(key):
            with sl.write(key):
                results.append(key)

        threads = [threading.Thread(target=work, args=(f"k{i}",)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(len(results), 20)

    def test_num_stripes_property(self):
        self.assertEqual(StripedLock(8).num_stripes, 8)


if __name__ == "__main__":
    unittest.main()
