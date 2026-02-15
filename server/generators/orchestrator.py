"""生成编排器 - 核心协调模块"""
import json
import logging
from pathlib import Path

from config import Config
from generators.models import ProjectContext

logger = logging.getLogger(__name__)


class StepFatalError(Exception):
    """致命错误 - 无法继续，终止整个流程"""
    pass


class StepWarningError(Exception):
    """警告错误 - 当前步骤部分失败，但可以继续后续步骤"""
    pass


class Orchestrator:
    """六步生成流程编排器"""

    def __init__(self, task_manager):
        self.task_manager = task_manager

    def run(self, task_id: str, context: ProjectContext):
        """执行生成流程，支持断点恢复"""
        checkpoint = self._load_checkpoint(task_id)
        start_step = checkpoint.get('completed_step', 0) + 1

        steps = [
            (1, "生成功能清单", self._step1_generate_features),
            (2, "生成源代码", self._step2_generate_code),
            (3, "生成HTML页面", self._step3_generate_html),
            (4, "页面截图", self._step4_take_screenshots),
            (5, "生成文档", self._step5_generate_docs),
            (6, "打包下载", self._step6_package),
        ]

        for step_num, step_name, step_func in steps:
            if step_num < start_step:
                self._log(task_id, f"跳过已完成步骤: {step_name}")
                continue

            try:
                self._update_progress(task_id, step_num, step_name, "processing")
                self._log(task_id, f"开始步骤{step_num}: {step_name}")
                step_func(task_id, context)
                self._save_checkpoint(task_id, step_num, context)
                self._log(task_id, f"步骤{step_num}完成: {step_name}")
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

        # 全部完成
        self._log(task_id, "所有步骤完成")

    def _step1_generate_features(self, task_id: str, context: ProjectContext):
        """步骤1: AI生成功能清单"""
        self._log(task_id, "正在分析项目需求，生成功能清单...")
        # TODO: Phase 3 实现AI功能清单生成
        # 临时使用占位数据
        from generators.models import Feature
        context.feature_list = [
            Feature(name="用户登录", description="系统登录认证功能", page_type="login", manual_section="4.2.1"),
            Feature(name="系统首页", description="数据概览仪表盘", page_type="dashboard", manual_section="4.2.2"),
            Feature(name="数据管理", description="核心数据的增删改查", page_type="list", manual_section="4.2.3"),
            Feature(name="数据录入", description="新增和编辑数据表单", page_type="form", manual_section="4.2.4"),
            Feature(name="详情查看", description="数据详细信息展示", page_type="detail", manual_section="4.2.5"),
            Feature(name="统计分析", description="数据统计图表展示", page_type="chart", manual_section="4.2.6"),
        ]
        context.feature_summary = "、".join(f.name for f in context.feature_list)
        self._update_progress(task_id, 1, "生成功能清单", 100, "功能清单生成完成")

    def _step2_generate_code(self, task_id: str, context: ProjectContext):
        """步骤2: 混合生成源代码"""
        self._log(task_id, "正在生成源代码...")
        # TODO: Phase 3 实现混合代码生成
        self._update_progress(task_id, 2, "生成源代码", 100, "源代码生成完成")

    def _step3_generate_html(self, task_id: str, context: ProjectContext):
        """步骤3: 生成HTML静态页面"""
        self._log(task_id, "正在生成页面...")
        # TODO: Phase 4 实现HTML页面生成
        self._update_progress(task_id, 3, "生成HTML页面", 100, "HTML页面生成完成")

    def _step4_take_screenshots(self, task_id: str, context: ProjectContext):
        """步骤4: Playwright批量截图"""
        self._log(task_id, "正在截图...")
        # TODO: Phase 4 实现截图服务
        self._update_progress(task_id, 4, "页面截图", 100, "截图完成")

    def _step5_generate_docs(self, task_id: str, context: ProjectContext):
        """步骤5: 生成3个Word文档"""
        self._log(task_id, "正在生成Word文档...")
        # TODO: Phase 4 实现文档生成
        self._update_progress(task_id, 5, "生成文档", 100, "文档生成完成")

    def _step6_package(self, task_id: str, context: ProjectContext):
        """步骤6: 打包ZIP"""
        self._log(task_id, "正在打包...")
        # TODO: 实现打包逻辑
        output_files = {}
        self.task_manager.complete_task(task_id, output_files)
        self._update_progress(task_id, 6, "打包下载", 100, "打包完成")

    def _update_progress(self, task_id: str, step: int, name: str, progress=0, message=""):
        """更新进度"""
        msg = message or f"正在执行: {name}"
        self.task_manager.update_progress(task_id, step, name, progress, msg)

    def _log(self, task_id: str, message: str):
        """记录日志"""
        logger.info(f"[{task_id}] {message}")
        self.task_manager.add_log(task_id, message)

    def _save_checkpoint(self, task_id: str, step: int, context: ProjectContext):
        """保存断点"""
        checkpoint_dir = Config.TASK_DATA_DIR / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "completed_step": step,
            "context": context.to_dict(),
        }
        filepath = checkpoint_dir / f"{task_id}_checkpoint.json"
        filepath.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding='utf-8')

    def _load_checkpoint(self, task_id: str) -> dict:
        """加载断点"""
        filepath = Config.TASK_DATA_DIR / "checkpoints" / f"{task_id}_checkpoint.json"
        if filepath.exists():
            try:
                return json.loads(filepath.read_text(encoding='utf-8'))
            except Exception:
                pass
        return {}
