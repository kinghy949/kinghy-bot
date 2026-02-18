"""轻量级任务管理器 - 线程池执行 + JSON文件持久化"""
import uuid
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self, max_workers=2, data_dir="./data/tasks"):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict = {}
        self._futures: dict = {}
        self._load_from_disk()

    def submit_task(self, run_func, context) -> str:
        """提交生成任务，返回task_id"""
        task_id = str(uuid.uuid4())[:8]
        task_state = {
            "task_id": task_id,
            "status": "pending",
            "cancel_requested": False,
            "current_step": 0,
            "total_steps": 6,
            "step_name": "",
            "progress": 0,
            "message": "任务已创建，等待执行...",
            "created_at": datetime.now().isoformat(),
            "context": context.to_dict(),
            "warnings": [],
            "errors": [],
            "output_files": {},
            "logs": [],
        }
        self._save_state(task_id, task_state)

        future = self.executor.submit(run_func, task_id, context)
        future.add_done_callback(lambda f: self._on_task_done(task_id, f))
        self._futures[task_id] = future
        return task_id

    def get_task_state(self, task_id: str) -> dict | None:
        """获取任务状态"""
        if task_id in self._cache:
            return self._cache[task_id]
        return self._load_state(task_id)

    def update_progress(self, task_id: str, step: int, name: str, progress: int, message: str):
        """更新任务进度"""
        state = self.get_task_state(task_id)
        if not state:
            return
        state.update({
            "status": "processing",
            "current_step": step,
            "step_name": name,
            "progress": progress,
            "message": message,
        })
        self._save_state(task_id, state)

    def add_log(self, task_id: str, log_message: str):
        """添加日志"""
        state = self.get_task_state(task_id)
        if not state:
            return
        state["logs"].append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": log_message,
        })
        self._save_state(task_id, state)

    def add_warning(self, task_id: str, warning: str):
        """添加警告"""
        state = self.get_task_state(task_id)
        if not state:
            return
        state["warnings"].append(warning)
        self._save_state(task_id, state)

    def complete_task(self, task_id: str, output_files: dict):
        """标记任务完成"""
        state = self.get_task_state(task_id)
        if not state:
            return
        state.update({
            "status": "completed",
            "current_step": 6,
            "progress": 100,
            "message": "生成完成",
            "output_files": output_files,
        })
        self._save_state(task_id, state)

    def mark_cancelled(self, task_id: str, message: str = "任务已取消"):
        state = self.get_task_state(task_id)
        if not state:
            return
        state.update({
            "status": "cancelled",
            "message": message,
            "cancel_requested": True,
        })
        self._save_state(task_id, state)

    def fail_task(self, task_id: str, error_message: str):
        """标记任务失败"""
        state = self.get_task_state(task_id)
        if not state:
            return
        state.update({
            "status": "failed",
            "message": error_message,
        })
        state["errors"].append(error_message)
        self._save_state(task_id, state)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        state = self.get_task_state(task_id)
        if not state:
            return False
        if state.get("status") in ("completed", "failed", "cancelled"):
            return False
        state["cancel_requested"] = True
        state["message"] = "已收到取消请求，正在停止任务..."
        self._save_state(task_id, state)

        if task_id in self._futures:
            cancelled = self._futures[task_id].cancel()
            if cancelled:
                self.mark_cancelled(task_id, "任务已取消")
            return True
        return True

    def is_cancel_requested(self, task_id: str) -> bool:
        state = self.get_task_state(task_id)
        if not state:
            return False
        return bool(state.get("cancel_requested"))

    def _on_task_done(self, task_id: str, future):
        """任务完成回调"""
        try:
            exc = future.exception()
            if exc:
                logger.error(f"任务 {task_id} 异常: {exc}")
                self.fail_task(task_id, str(exc))
        except Exception as e:
            logger.error(f"处理任务回调异常: {e}")
        finally:
            self._futures.pop(task_id, None)

    def _save_state(self, task_id: str, state: dict):
        """持久化到JSON文件 + 更新内存缓存"""
        self._cache[task_id] = state
        filepath = self.data_dir / f"{task_id}.json"
        try:
            filepath.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"保存任务状态失败: {e}")

    def _load_state(self, task_id: str) -> dict | None:
        filepath = self.data_dir / f"{task_id}.json"
        if filepath.exists():
            try:
                state = json.loads(filepath.read_text(encoding='utf-8'))
                self._cache[task_id] = state
                return state
            except Exception:
                pass
        return None

    def _load_from_disk(self):
        """启动时从磁盘恢复任务状态"""
        for f in self.data_dir.glob("*.json"):
            try:
                state = json.loads(f.read_text(encoding='utf-8'))
                tid = state.get("task_id")
                if tid:
                    # 恢复时将processing状态标记为interrupted
                    if state.get("status") == "processing":
                        state["status"] = "interrupted"
                        state["message"] = "任务被中断，可尝试恢复"
                    self._cache[tid] = state
            except Exception:
                pass
