import threading
import time
import unittest

from cachelite.sync.rwlock import ReadWriteLock


class TestReadWriteLock(unittest.TestCase):
    def test_multiple_concurrent_readers(self):
        lock = ReadWriteLock()
        active = []
        peak = [0]
        b = threading.Barrier(3)

        def reader():
            with lock.read():
                b.wait()
                active.append(1)
                peak[0] = max(peak[0], len(active))
                time.sleep(0.05)
                active.pop()

        threads = [threading.Thread(target=reader) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(peak[0], 3)  # all three read at once

    def test_writer_excludes_readers(self):
        lock = ReadWriteLock()
        order = []

        def writer():
            with lock.write():
                order.append("w-start")
                time.sleep(0.1)
                order.append("w-end")

        def reader():
            time.sleep(0.02)  # ensure writer goes first
            with lock.read():
                order.append("r")

        tw = threading.Thread(target=writer)
        tr = threading.Thread(target=reader)
        tw.start()
        tr.start()
        tw.join()
        tr.join()
        # reader must not interleave between writer start and end
        self.assertEqual(order, ["w-start", "w-end", "r"])

    def test_release_without_acquire_raises(self):
        lock = ReadWriteLock()
        with self.assertRaises(RuntimeError):
            lock.read_release()

    def test_sequential_write_acquire_release(self):
        lock = ReadWriteLock()
        lock.write_acquire()
        lock.write_release()
        lock.write_acquire()
        lock.write_release()

    def test_no_deadlock_under_mixed_load(self):
        lock = ReadWriteLock()
        counter = {"v": 0}

        def writer():
            for _ in range(100):
                with lock.write():
                    counter["v"] += 1

        def reader():
            for _ in range(100):
                with lock.read():
                    _ = counter["v"]

        threads = [threading.Thread(target=writer) for _ in range(2)]
        threads += [threading.Thread(target=reader) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
            self.assertFalse(t.is_alive())
        self.assertEqual(counter["v"], 200)


if __name__ == "__main__":
    unittest.main()
