"""代码检查器单测。"""
import unittest

from generators.code_checker import CodeChecker


class TestCodeChecker(unittest.TestCase):
    def test_check_stats_and_languages(self):
        checker = CodeChecker()
        generated_code = {
            "backend/app.py": "print('a')\nprint('b')\n",
            "frontend/src/App.vue": "<template>\n  <div>ok</div>\n</template>\n",
            "README.md": "# title\n",
        }

        result = checker.check(generated_code, target_lines=20)

        self.assertEqual(result.file_count, 3)
        self.assertEqual(result.total_lines, 9)
        self.assertTrue(result.needs_expansion)
        self.assertEqual(result.languages, ["Markdown", "Python", "Vue"])

    def test_no_expansion_when_meet_threshold(self):
        checker = CodeChecker()
        generated_code = {
            "a.py": "\n".join(["line"] * 9),
        }
        result = checker.check(generated_code, target_lines=10)
        self.assertFalse(result.needs_expansion)


if __name__ == "__main__":
    unittest.main()
