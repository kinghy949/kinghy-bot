"""截图服务降级测试。"""
import tempfile
import unittest
from pathlib import Path

from config import Config
from generators.screenshot_service import ScreenshotService


class TestScreenshotService(unittest.TestCase):
    def test_fallback_placeholder_when_html_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_shots = Config.SCREENSHOT_DIR
            Config.SCREENSHOT_DIR = Path(temp_dir) / "shots"
            try:
                service = ScreenshotService()
                result = service.take_screenshots("task1", {"功能A": "D:/not-exists.html"})
                shot_path = Path(result["功能A"])
                self.assertTrue(shot_path.exists())
                self.assertIn("placeholder", shot_path.name)
            finally:
                Config.SCREENSHOT_DIR = old_shots


if __name__ == "__main__":
    unittest.main()
