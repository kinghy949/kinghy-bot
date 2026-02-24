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
    """七步生成流程编排器"""
    QUALITY_RETRY_LIMIT = 1
    RECOVERABLE_QUALITY_RULES = {"MAN-002", "MAN-000", "CODE-000"}

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
            (6, "文档规范检查", self._step6_quality_gate),
            (7, "打包下载", self._step7_package),
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
        for idx, feature in enumerate(context.feature_list, start=1):
            if not feature.feature_id:
                feature.feature_id = f"F{idx:02d}"
            if not feature.manual_section:
                feature.manual_section = f"4.4.{idx}"
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

        source_path = self.source_doc_generator.generate(task_id, context)
        manual_path = self.manual_doc_generator.generate(task_id, context)
        app_path = self.application_doc_generator.generate(task_id, context)

        context.output_files = {
            "source": source_path,
            "manual": manual_path,
            "application": app_path,
        }
        self._update_progress(task_id, 5, "生成文档", 100, "三份文档生成完成")

    def _step6_quality_gate(self, task_id: str, context: ProjectContext):
        self._log(task_id, "执行文档规范检查...")
        report = self.consistency_checker.check(context)
        if report.errors:
            rule_ids = self._extract_error_rule_ids(report.errors)
            if self._can_retry_quality_gate(rule_ids):
                self._log(task_id, f"质量检查未通过，触发自动重试1次。规则: {', '.join(sorted(rule_ids))}")
                self._update_progress(task_id, 6, "文档规范检查", 60, "首次检查未通过，正在自动重试...")
                self._run_quality_remediation(task_id, context, rule_ids)
                report = self.consistency_checker.check(context)

        for warning in report.warnings:
            self.task_manager.add_warning(task_id, warning)

        quality_report_path = self._write_quality_report(task_id, context, report)
        context.output_files["quality_report"] = quality_report_path
        context.doc_metrics["quality"] = {
            "score": report.score,
            "errors": report.errors,
            "warnings": report.warnings,
            "checks": report.checks,
        }
        if report.errors:
            for suggestion in self.consistency_checker.get_suggestions(context, report):
                self.task_manager.add_warning(task_id, f"人工补充建议：{suggestion}")
            raise StepFatalError("; ".join(report.errors))

        self._update_progress(task_id, 6, "文档规范检查", 100, f"检查通过，质量评分: {report.score}")

    def _step7_package(self, task_id: str, context: ProjectContext):
        self._log(task_id, "整理下载文件...")
        output_files = context.output_files
        if not output_files:
            raise StepFatalError("未生成可下载文件")
        self._update_progress(task_id, 7, "打包下载", 100, "打包完成")
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

    def _write_quality_report(self, task_id: str, context: ProjectContext, report) -> str:
        output_dir = Config.OUTPUT_DIR / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "quality_report.md"
        report_path.write_text(
            self.consistency_checker.build_quality_report_md(context, report),
            encoding="utf-8",
        )
        return str(report_path)

    def _extract_error_rule_ids(self, errors: list[str]) -> set[str]:
        rule_ids: set[str] = set()
        for item in errors:
            if item.startswith("[") and "]" in item:
                rule_ids.add(item[1:item.find("]")])
        return rule_ids

    def _can_retry_quality_gate(self, rule_ids: set[str]) -> bool:
        if not rule_ids:
            return False
        return rule_ids.issubset(self.RECOVERABLE_QUALITY_RULES)

    def _run_quality_remediation(self, task_id: str, context: ProjectContext, rule_ids: set[str]):
        if "MAN-002" in rule_ids and context.generated_html_pages:
            self._log(task_id, "执行重试修复：重新截图并刷新说明文档。")
            shots = self.screenshot_service.take_screenshots(task_id, context.generated_html_pages)
            context.screenshots = shots
            for feature in context.feature_list:
                feature.screenshot_path = shots.get(feature.name, feature.screenshot_path)
            manual_path = self.manual_doc_generator.generate(task_id, context)
            context.output_files["manual"] = manual_path

        if "MAN-000" in rule_ids:
            self._log(task_id, "执行重试修复：重建说明文档。")
            context.output_files["manual"] = self.manual_doc_generator.generate(task_id, context)

        if "CODE-000" in rule_ids:
            self._log(task_id, "执行重试修复：重建源码文档。")
            context.output_files["source"] = self.source_doc_generator.generate(task_id, context)
