import time
import unittest

from cachelite import Cache, cached


class TestCachedDecorator(unittest.TestCase):
    def test_memoizes_results(self):
        calls = {"n": 0}
        c = Cache(max_items=100)

        @cached(c)
        def square(x):
            calls["n"] += 1
            return x * x

        self.assertEqual(square(4), 16)
        self.assertEqual(square(4), 16)
        self.assertEqual(calls["n"], 1)  # second call hit cache

    def test_different_args_different_keys(self):
        c = Cache(max_items=100)

        @cached(c)
        def add(a, b):
            return a + b

        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(c.size(), 2)

    def test_kwargs_order_independent(self):
        calls = {"n": 0}
        c = Cache(max_items=100)

        @cached(c)
        def f(a=1, b=2):
            calls["n"] += 1
            return a + b

        f(a=1, b=2)
        f(b=2, a=1)  # same call, different order
        self.assertEqual(calls["n"], 1)

    def test_ttl_expiry(self):
        calls = {"n": 0}
        c = Cache(max_items=100)

        @cached(c, ttl=0.1)
        def f(x):
            calls["n"] += 1
            return x

        f(5)
        time.sleep(0.15)
        f(5)  # cache expired, recompute
        self.assertEqual(calls["n"], 2)

    def test_caches_none_return(self):
        calls = {"n": 0}
        c = Cache(max_items=100)

        @cached(c)
        def f(x):
            calls["n"] += 1
            return None

        f(1)
        f(1)
        self.assertEqual(calls["n"], 1)  # None was cached, not re-run

    def test_cache_clear(self):
        calls = {"n": 0}
        c = Cache(max_items=100)

        @cached(c)
        def f(x):
            calls["n"] += 1
            return x

        f(1)
        f.cache_clear()
        f(1)
        self.assertEqual(calls["n"], 2)

    def test_custom_key_fn(self):
        c = Cache(max_items=100)

        @cached(c, key_fn=lambda user, **kw: f"user:{user['id']}")
        def get_profile(user):
            return user["name"]

        get_profile({"id": 1, "name": "Ada"})
        self.assertIn("user:1", c.keys())

    def test_cache_info(self):
        c = Cache(max_items=100)

        @cached(c)
        def f(x):
            return x

        f(1)
        f(1)
        self.assertEqual(f.cache_info().hits, 1)

    def test_wrapped_attribute(self):
        c = Cache(max_items=10)

        @cached(c)
        def f(x):
            return x

        self.assertTrue(hasattr(f, "__wrapped__"))


if __name__ == "__main__":
    unittest.main()
