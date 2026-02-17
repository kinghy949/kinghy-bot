"""文件清理工具：定时清理过期任务与产物文件。"""
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path


logger = logging.getLogger(__name__)


class FileManager:
    """文件管理器：按保留时长清理历史产物。"""

    def __init__(self, output_dir: Path, screenshot_dir: Path, task_data_dir: Path, retention_hours: int):
        self.output_dir = Path(output_dir)
        self.screenshot_dir = Path(screenshot_dir)
        self.task_data_dir = Path(task_data_dir)
        self.retention_hours = max(1, int(retention_hours))

    def cleanup_once(self, now: datetime | None = None) -> dict:
        """执行一次清理，返回清理统计。"""
        now = now or datetime.now()
        cutoff = now - timedelta(hours=self.retention_hours)

        stats = {
            "output_removed": 0,
            "screenshot_removed": 0,
            "task_removed": 0,
            "checkpoint_removed": 0,
            "errors": 0,
        }

        stats["output_removed"] = self._cleanup_paths(self.output_dir, cutoff)
        stats["screenshot_removed"] = self._cleanup_paths(self.screenshot_dir, cutoff)

        stats["task_removed"] = self._cleanup_files(self.task_data_dir, cutoff, "*.json")
        checkpoint_dir = self.task_data_dir / "checkpoints"
        stats["checkpoint_removed"] = self._cleanup_files(checkpoint_dir, cutoff, "*.json")

        self._cleanup_empty_dirs(self.output_dir)
        self._cleanup_empty_dirs(self.screenshot_dir)
        self._cleanup_empty_dirs(checkpoint_dir)

        return stats

    def _cleanup_paths(self, base_dir: Path, cutoff: datetime) -> int:
        if not base_dir.exists():
            return 0
        removed = 0
        for path in sorted(base_dir.iterdir()):
            if path.name == ".gitkeep":
                continue
            if self._is_expired(path, cutoff):
                try:
                    if path.is_dir():
                        for child in sorted(path.rglob("*"), reverse=True):
                            if child.is_file():
                                child.unlink(missing_ok=True)
                            elif child.is_dir():
                                child.rmdir()
                        path.rmdir()
                    else:
                        path.unlink(missing_ok=True)
                    removed += 1
                except Exception as exc:
                    logger.warning("清理路径失败 %s: %s", path, exc)
        return removed

    def _cleanup_files(self, base_dir: Path, cutoff: datetime, pattern: str) -> int:
        if not base_dir.exists():
            return 0
        removed = 0
        for file_path in base_dir.glob(pattern):
            if file_path.name == ".gitkeep":
                continue
            if self._is_expired(file_path, cutoff):
                try:
                    file_path.unlink(missing_ok=True)
                    removed += 1
                except Exception as exc:
                    logger.warning("清理文件失败 %s: %s", file_path, exc)
        return removed

    def _cleanup_empty_dirs(self, base_dir: Path):
        if not base_dir.exists():
            return
        for dir_path in sorted(base_dir.rglob("*"), reverse=True):
            if not dir_path.is_dir():
                continue
            try:
                next(dir_path.iterdir())
            except StopIteration:
                dir_path.rmdir()
            except Exception:
                continue

    def _is_expired(self, path: Path, cutoff: datetime) -> bool:
        try:
            modified_time = datetime.fromtimestamp(path.stat().st_mtime)
            return modified_time < cutoff
        except Exception:
            return False


class FileCleanupWorker:
    """后台文件清理线程。"""

    def __init__(self, file_manager: FileManager, interval_minutes: int = 60):
        self.file_manager = file_manager
        self.interval_seconds = max(60, int(interval_minutes) * 60)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="file-cleanup-worker")

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                stats = self.file_manager.cleanup_once()
                logger.info("文件清理完成: %s", stats)
            except Exception as exc:
                logger.error("文件清理异常: %s", exc)
            self._stop_event.wait(self.interval_seconds)

