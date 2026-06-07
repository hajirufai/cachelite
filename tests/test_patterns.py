import unittest

from cachelite.patterns import compile_pattern, filter_keys, matches


class TestPatterns(unittest.TestCase):
    def test_star_matches_anything_including_colon(self):
        self.assertTrue(matches("user:42:profile", "user:*"))
        self.assertTrue(matches("user:1", "user:*"))

    def test_exact_match(self):
        self.assertTrue(matches("foo", "foo"))
        self.assertFalse(matches("foobar", "foo"))

    def test_question_mark_single_char(self):
        self.assertTrue(matches("cat", "ca?"))
        self.assertFalse(matches("cart", "ca?"))

    def test_char_class(self):
        self.assertTrue(matches("file1", "file[0-9]"))
        self.assertFalse(matches("filea", "file[0-9]"))

    def test_case_sensitive(self):
        self.assertFalse(matches("User", "user*"))

    def test_filter_keys(self):
        keys = ["user:1", "user:2", "post:1", "comment:5"]
        result = sorted(filter_keys(keys, "user:*"))
        self.assertEqual(result, ["user:1", "user:2"])

    def test_compile_pattern_reuse(self):
        rx = compile_pattern("session:*")
        self.assertTrue(rx.match("session:abc"))
        self.assertIsNone(rx.match("user:abc"))

    def test_no_matches(self):
        self.assertEqual(list(filter_keys(["a", "b"], "z*")), [])


if __name__ == "__main__":
    unittest.main()
