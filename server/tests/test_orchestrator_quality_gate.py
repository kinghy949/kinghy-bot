"""编排器文档规范检查阶段测试。"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from config import Config
from generators.consistency_checker import ConsistencyReport
from generators.models import Feature, ProjectContext
from generators.orchestrator import Orchestrator, StepFatalError


class _FakeTaskManager:
    def __init__(self):
        self.warnings: list[str] = []
        self.logs: list[str] = []
        self.progress: list[dict] = []

    def add_warning(self, task_id: str, warning: str):
        self.warnings.append(warning)

    def add_log(self, task_id: str, message: str):
        self.logs.append(message)

    def update_progress(self, task_id: str, step: int, name: str, progress: int, message: str):
        self.progress.append({"step": step, "name": name, "progress": progress, "message": message})


class TestOrchestratorQualityGate(unittest.TestCase):
    def _base_context(self) -> ProjectContext:
        context = ProjectContext(
            software_name="系统A",
            short_name="系统A",
            description="d",
            tech_stack_id="flask_vue",
            target_lines=100,
        )
        context.total_lines = 100
        context.feature_list = [
            Feature(name="用户登录", description="d", page_type="login", feature_id="F01", manual_section="4.1.1", code_files=["a.py"], screenshot_path="real.png")
        ]
        context.output_files = {"source": "a.docx", "manual": "b.docx", "application": "c.docx"}
        context.doc_metrics = {
            "source": {
                "strategy": "full",
                "total_code_lines": 100,
                "selected_code_lines": 100,
                "selected_files": ["a.py"],
                "page_limit": 70,
                "lines_per_page": 50,
                "estimated_pages": 2,
                "last_file_complete": True,
                "traceability": {
                    "feature_to_files": {"F01": ["a.py"]},
                    "file_to_features": {"a.py": ["F01"]},
                },
            },
            "manual": {
                "required_sections": ["登录", "主界面", "界面跳转", "主要功能模块"],
                "required_sections_complete": True,
                "missing_screenshots": [],
                "feature_screenshot_coverage": 1,
                "feature_total": 1,
                "traceability": {
                    "F01": {
                        "manual_section": "4.1.1",
                        "feature_name": "用户登录",
                        "code_files": ["a.py"],
                    }
                },
            },
        }
        return context

    def test_quality_gate_success_writes_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_output = Config.OUTPUT_DIR
            Config.OUTPUT_DIR = Path(temp_dir)
            try:
                tm = _FakeTaskManager()
                orchestrator = Orchestrator(tm)
                context = self._base_context()
                orchestrator._step6_quality_gate("task_ok", context)
                report_path = Path(context.output_files["quality_report"])
                self.assertTrue(report_path.exists())
                self.assertTrue(any(item["step"] == 6 for item in tm.progress))
            finally:
                Config.OUTPUT_DIR = old_output

    def test_quality_gate_failure_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_output = Config.OUTPUT_DIR
            Config.OUTPUT_DIR = Path(temp_dir)
            try:
                tm = _FakeTaskManager()
                orchestrator = Orchestrator(tm)
                context = self._base_context()
                context.doc_metrics["manual"]["missing_screenshots"] = ["用户登录"]
                with self.assertRaises(StepFatalError):
                    orchestrator._step6_quality_gate("task_fail", context)
                self.assertIn("quality_report", context.output_files)
            finally:
                Config.OUTPUT_DIR = old_output

    def test_quality_gate_retry_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_output = Config.OUTPUT_DIR
            Config.OUTPUT_DIR = Path(temp_dir)
            try:
                tm = _FakeTaskManager()
                orchestrator = Orchestrator(tm)
                context = self._base_context()
                context.generated_html_pages = {"用户登录": str(Path(temp_dir) / "login.html")}
                Path(context.generated_html_pages["用户登录"]).write_text("<html></html>", encoding="utf-8")

                first = ConsistencyReport(errors=["[MAN-002] 主要功能截图缺失: 用户登录"], warnings=[], checks=[], score=70)
                second = ConsistencyReport(errors=[], warnings=[], checks=[], score=95)
                orchestrator.consistency_checker.check = Mock(side_effect=[first, second])
                orchestrator.consistency_checker.build_quality_report_md = Mock(return_value="# report\n")
                orchestrator.consistency_checker.get_suggestions = Mock(return_value=["补图"])
                orchestrator.screenshot_service.take_screenshots = Mock(return_value={"用户登录": "real.png"})
                orchestrator.manual_doc_generator.generate = Mock(return_value="manual_retry.docx")

                orchestrator._step6_quality_gate("task_retry_ok", context)
                self.assertEqual(orchestrator.consistency_checker.check.call_count, 2)
                self.assertIn("quality_report", context.output_files)
                self.assertTrue(any("自动重试" in m["message"] for m in tm.progress))
            finally:
                Config.OUTPUT_DIR = old_output


if __name__ == "__main__":
    unittest.main()
