import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from cachelite.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = os.path.join(self.tmp, "store.json")

    def _run(self, args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(args)
        return code, out.getvalue()

    def test_set_get_roundtrip(self):
        code, _ = self._run(["--store", self.store, "set", "k", "42"])
        self.assertEqual(code, 0)
        code, out = self._run(["--store", self.store, "get", "k"])
        self.assertEqual(code, 0)
        self.assertIn("42", out)

    def test_set_json_value(self):
        self._run(["--store", self.store, "set", "u", '{"name":"Ada"}'])
        code, out = self._run(["--store", self.store, "get", "u"])
        self.assertIn("Ada", out)

    def test_get_missing_returns_1(self):
        code, _ = self._run(["--store", self.store, "get", "ghost"])
        self.assertEqual(code, 1)

    def test_delete(self):
        self._run(["--store", self.store, "set", "k", "1"])
        code, out = self._run(["--store", self.store, "delete", "k"])
        self.assertEqual(code, 0)
        self.assertIn("deleted", out)

    def test_keys_pattern(self):
        self._run(["--store", self.store, "set", "user:1", "1"])
        self._run(["--store", self.store, "set", "post:1", "2"])
        code, out = self._run(["--store", self.store, "keys", "user:*"])
        self.assertIn("user:1", out)
        self.assertNotIn("post:1", out)

    def test_flush(self):
        self._run(["--store", self.store, "set", "k", "1"])
        code, out = self._run(["--store", self.store, "flush"])
        self.assertIn("cleared", out)

    def test_stats(self):
        self._run(["--store", self.store, "set", "k", "1"])
        code, out = self._run(["--store", self.store, "stats"])
        self.assertIn("items", out)

    def test_demo_runs(self):
        code, out = self._run(["demo"])
        self.assertEqual(code, 0)
        self.assertIn("CacheLite demo", out)


if __name__ == "__main__":
    unittest.main()
