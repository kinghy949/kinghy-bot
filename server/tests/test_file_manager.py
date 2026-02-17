"""文件清理器单测。"""
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from utils.file_manager import FileManager


class TestFileManager(unittest.TestCase):
    def test_cleanup_expired_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            screenshot_dir = root / "screenshots"
            task_data_dir = root / "tasks"
            checkpoint_dir = task_data_dir / "checkpoints"

            for d in [output_dir, screenshot_dir, task_data_dir, checkpoint_dir]:
                d.mkdir(parents=True, exist_ok=True)

            (output_dir / ".gitkeep").write_text("", encoding="utf-8")
            old_output = output_dir / "old.txt"
            old_output.write_text("old", encoding="utf-8")
            new_output = output_dir / "new.txt"
            new_output.write_text("new", encoding="utf-8")

            old_shot = screenshot_dir / "old.png"
            old_shot.write_text("old", encoding="utf-8")
            old_task = task_data_dir / "old_task.json"
            old_task.write_text("{}", encoding="utf-8")
            old_checkpoint = checkpoint_dir / "old_cp.json"
            old_checkpoint.write_text("{}", encoding="utf-8")

            past = datetime.now() - timedelta(hours=5)
            os.utime(old_output, (past.timestamp(), past.timestamp()))
            os.utime(old_shot, (past.timestamp(), past.timestamp()))
            os.utime(old_task, (past.timestamp(), past.timestamp()))
            os.utime(old_checkpoint, (past.timestamp(), past.timestamp()))

            manager = FileManager(
                output_dir=output_dir,
                screenshot_dir=screenshot_dir,
                task_data_dir=task_data_dir,
                retention_hours=1,
            )
            stats = manager.cleanup_once()

            self.assertEqual(stats["output_removed"], 1)
            self.assertEqual(stats["screenshot_removed"], 1)
            self.assertEqual(stats["task_removed"], 1)
            self.assertEqual(stats["checkpoint_removed"], 1)

            self.assertFalse(old_output.exists())
            self.assertFalse(old_shot.exists())
            self.assertFalse(old_task.exists())
            self.assertFalse(old_checkpoint.exists())
            self.assertTrue(new_output.exists())
            self.assertTrue((output_dir / ".gitkeep").exists())


if __name__ == "__main__":
    unittest.main()
