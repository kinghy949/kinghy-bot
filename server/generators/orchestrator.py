"""生成编排器 - 核心协调模块"""
import json
import logging

from config import Config
from generators.application_doc_generator import ApplicationDocGenerator
from generators.code_generator import CodeGenerator
from generators.consistency_checker import ConsistencyChecker
from generators.feature_generator import FeatureGenerator
from generators.html_page_generator import HtmlPageGenerator
from generators.manual_doc_generator import ManualDocGenerator
from generators.models import ProjectContext
from generators.screenshot_service import ScreenshotService
from generators.source_doc_generator import SourceDocGenerator

logger = logging.getLogger(__name__)


class StepFatalError(Exception):
    """致命错误 - 无法继续，终止整个流程"""


class StepWarningError(Exception):
    """警告错误 - 当前步骤部分失败，但可以继续后续步骤"""


class TaskCancelledError(Exception):
    """任务被取消"""


class Orchestrator:
    """六步生成流程编排器"""

    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.feature_generator = FeatureGenerator()
        self.code_generator = CodeGenerator()
        self.html_generator = HtmlPageGenerator()
        self.screenshot_service = ScreenshotService()
        self.source_doc_generator = SourceDocGenerator()
        self.manual_doc_generator = ManualDocGenerator()
        self.application_doc_generator = ApplicationDocGenerator()
        self.consistency_checker = ConsistencyChecker()

    def run(self, task_id: str, context: ProjectContext):
        checkpoint = self._load_checkpoint(task_id)
        if checkpoint.get("context"):
            try:
                context = ProjectContext.from_dict(checkpoint["context"])
            except Exception:
                pass

        start_step = checkpoint.get("completed_step", 0) + 1
        steps = [
            (1, "生成功能清单", self._step1_generate_features),
            (2, "生成源代码", self._step2_generate_code),
            (3, "生成HTML页面", self._step3_generate_html),
            (4, "页面截图", self._step4_take_screenshots),
            (5, "生成文档", self._step5_generate_docs),
            (6, "打包下载", self._step6_package),
        ]

        for step_num, step_name, step_func in steps:
            self._check_cancel(task_id, f"步骤{step_num}开始前收到取消请求")
            if step_num < start_step:
                self._log(task_id, f"跳过已完成步骤: {step_name}")
                continue

            try:
                self._update_progress(task_id, step_num, step_name, 5, f"开始步骤{step_num}: {step_name}")
                step_func(task_id, context)
                self._check_cancel(task_id, f"步骤{step_num}执行后收到取消请求")
                self._save_checkpoint(task_id, step_num, context)
                self._log(task_id, f"步骤{step_num}完成: {step_name}")
            except TaskCancelledError as e:
                self._log(task_id, f"任务取消: {e}")
                self.task_manager.mark_cancelled(task_id, str(e))
                return
            except StepFatalError as e:
                self._log(task_id, f"步骤{step_num}致命错误: {e}")
                self.task_manager.fail_task(task_id, f"步骤{step_num} {step_name} 失败: {e}")
                raise
            except StepWarningError as e:
                self._log(task_id, f"步骤{step_num}部分失败: {e}")
                self.task_manager.add_warning(task_id, str(e))
                self._save_checkpoint(task_id, step_num, context)
            except Exception as e:
                self._log(task_id, f"步骤{step_num}未预期错误: {e}")
                self.task_manager.fail_task(task_id, f"步骤{step_num} {step_name} 异常: {e}")
                raise

        self._log(task_id, "所有步骤完成")

    def _step1_generate_features(self, task_id: str, context: ProjectContext):
        self._log(task_id, "正在分析项目需求，生成功能清单...")
        context.feature_list = self.feature_generator.generate(context.software_name, context.description)
        context.feature_summary = "、".join(f.name for f in context.feature_list)
        self._update_progress(task_id, 1, "生成功能清单", 100, f"功能清单生成完成，共{len(context.feature_list)}个功能")

    def _step2_generate_code(self, task_id: str, context: ProjectContext):
        self._log(task_id, "正在生成源代码...")
        generated_code = self.code_generator.generate(task_id, context)
        self._update_progress(task_id, 2, "生成源代码", 100, f"源代码生成完成，文件数: {len(generated_code)}，总行数: {context.total_lines}")

    def _step3_generate_html(self, task_id: str, context: ProjectContext):
        self._log(task_id, "正在生成HTML页面...")
        html_files = self.html_generator.generate(task_id, context)
        self._update_progress(task_id, 3, "生成HTML页面", 100, f"HTML页面生成完成，共{len(html_files)}个页面")

    def _step4_take_screenshots(self, task_id: str, context: ProjectContext):
        self._log(task_id, "正在截图...")
        shots = self.screenshot_service.take_screenshots(task_id, context.generated_html_pages)
        context.screenshots = shots
        for feature in context.feature_list:
            feature.screenshot_path = shots.get(feature.name, "")
        self._update_progress(task_id, 4, "页面截图", 100, f"截图完成，共{len(shots)}张")

    def _step5_generate_docs(self, task_id: str, context: ProjectContext):
        self._log(task_id, "正在生成Word文档...")

        report = self.consistency_checker.check(context)
        for warning in report.warnings:
            self.task_manager.add_warning(task_id, warning)
        if report.errors:
            raise StepFatalError("; ".join(report.errors))

        source_path = self.source_doc_generator.generate(task_id, context)
        manual_path = self.manual_doc_generator.generate(task_id, context)
        app_path = self.application_doc_generator.generate(task_id, context)

        context.output_files = {
            "source": source_path,
            "manual": manual_path,
            "application": app_path,
        }
        self._update_progress(task_id, 5, "生成文档", 100, "三份文档生成完成")

    def _step6_package(self, task_id: str, context: ProjectContext):
        self._log(task_id, "整理下载文件...")
        output_files = context.output_files
        if not output_files:
            raise StepFatalError("未生成可下载文件")
        self._update_progress(task_id, 6, "打包下载", 100, "打包完成")
        self.task_manager.complete_task(task_id, output_files)

    def _update_progress(self, task_id: str, step: int, name: str, progress=0, message=""):
        msg = message or f"正在执行: {name}"
        self.task_manager.update_progress(task_id, step, name, progress, msg)

    def _log(self, task_id: str, message: str):
        logger.info("[%s] %s", task_id, message)
        self.task_manager.add_log(task_id, message)

    def _save_checkpoint(self, task_id: str, step: int, context: ProjectContext):
        checkpoint_dir = Config.TASK_DATA_DIR / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint = {"completed_step": step, "context": context.to_dict()}
        filepath = checkpoint_dir / f"{task_id}_checkpoint.json"
        filepath.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_checkpoint(self, task_id: str) -> dict:
        filepath = Config.TASK_DATA_DIR / "checkpoints" / f"{task_id}_checkpoint.json"
        if filepath.exists():
            try:
                return json.loads(filepath.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _check_cancel(self, task_id: str, message: str):
        if self.task_manager.is_cancel_requested(task_id):
            raise TaskCancelledError(message)
