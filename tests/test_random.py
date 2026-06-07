import random
import unittest
from collections import Counter

from cachelite.errors import CacheEmptyError
from cachelite.eviction.random_evict import RandomPolicy


class TestRandomPolicy(unittest.TestCase):
    def test_evict_removes_a_member(self):
        p = RandomPolicy(rng=random.Random(0))
        for k in ["a", "b", "c"]:
            p.on_insert(k)
        victim = p.evict()
        self.assertIn(victim, {"a", "b", "c"})
        self.assertNotIn(victim, p)
        self.assertEqual(len(p), 2)

    def test_evict_empty_raises(self):
        with self.assertRaises(CacheEmptyError):
            RandomPolicy().evict()

    def test_remove_specific_key(self):
        p = RandomPolicy()
        for k in ["a", "b", "c"]:
            p.on_insert(k)
        p.on_remove("b")
        self.assertNotIn("b", p)
        self.assertEqual(len(p), 2)
        # remaining keys still evictable without error
        p.evict()
        p.evict()
        self.assertEqual(len(p), 0)

    def test_remove_missing_noop(self):
        p = RandomPolicy()
        p.on_insert("a")
        p.on_remove("ghost")
        self.assertEqual(len(p), 1)

    def test_duplicate_insert_ignored(self):
        p = RandomPolicy()
        p.on_insert("a")
        p.on_insert("a")
        self.assertEqual(len(p), 1)

    def test_index_integrity_after_swaps(self):
        # remove from middle many times; ensure no index corruption
        p = RandomPolicy(rng=random.Random(42))
        for i in range(100):
            p.on_insert(f"k{i}")
        for _ in range(50):
            p.evict()
        self.assertEqual(len(p), 50)
        # all remaining keys are unique and consistent
        for key in list(p._index):
            self.assertEqual(p._keys[p._index[key]], key)

    def test_roughly_uniform_distribution(self):
        counts = Counter()
        for seed in range(3000):
            p = RandomPolicy(rng=random.Random(seed))
            for k in ["a", "b", "c", "d"]:
                p.on_insert(k)
            counts[p.evict()] += 1
        # each of 4 keys should get ~750; allow generous slack
        for k in ["a", "b", "c", "d"]:
            self.assertGreater(counts[k], 500)

    def test_clear(self):
        p = RandomPolicy()
        p.on_insert("a")
        p.clear()
        self.assertEqual(len(p), 0)


if __name__ == "__main__":
    unittest.main()
