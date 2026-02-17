"""操作手册生成器"""
from pathlib import Path

from config import Config
from generators.models import ProjectContext


class ManualDocGenerator:
    def generate(self, task_id: str, context: ProjectContext) -> str:
        try:
            from docx import Document
            from docx.shared import Inches
        except ImportError:
            return self._fallback_text(task_id, context)

        doc = Document()
        doc.add_heading(context.software_name, level=0)
        doc.add_paragraph("操作手册")
        doc.add_paragraph(f"编写日期：{context.completion_date}")

        doc.add_heading("1. 引言", level=1)
        doc.add_paragraph(context.description)

        doc.add_heading("2. 运行环境", level=1)
        doc.add_paragraph(f"软件环境：{context.tech_config.get('runtime', '见部署说明')}")
        doc.add_paragraph(f"开发工具：{context.tech_config.get('dev_tools', '见部署说明')}")
        doc.add_paragraph(f"操作系统：{context.tech_config.get('os', 'Windows/Linux')}")

        doc.add_heading("3. 功能说明", level=1)
        for i, feature in enumerate(context.feature_list, start=1):
            doc.add_heading(f"3.{i} {feature.name}", level=2)
            doc.add_paragraph(feature.description)
            doc.add_paragraph(feature.operation_steps or "进入对应模块，根据页面提示完成操作。")

            shot = feature.screenshot_path
            if shot and Path(shot).exists():
                doc.add_picture(shot, width=Inches(6.0))
                doc.add_paragraph(f"图{i} {feature.name}界面")
            else:
                doc.add_paragraph("截图缺失，请后续补充真实截图。")

        out = Config.OUTPUT_DIR / task_id
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{self._safe(context.software_name)}_操作手册.docx"
        doc.save(path)
        return str(path)

    def _fallback_text(self, task_id: str, context: ProjectContext) -> str:
        out = Config.OUTPUT_DIR / task_id
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{self._safe(context.software_name)}_操作手册.txt"
        lines = [f"{context.software_name} 操作手册\n", f"编写日期：{context.completion_date}\n\n"]
        lines.append(f"项目背景：{context.description}\n\n")
        for i, feature in enumerate(context.feature_list, start=1):
            lines.append(f"{i}. {feature.name}\n")
            lines.append(f"说明：{feature.description}\n")
            lines.append(f"步骤：{feature.operation_steps or '进入页面执行操作'}\n")
            lines.append(f"截图：{feature.screenshot_path or '无'}\n\n")
        path.write_text("".join(lines), encoding="utf-8")
        return str(path)

    def _safe(self, name: str) -> str:
        return "".join(ch if ch not in '\\/:*?\"<>|' else "_" for ch in name).strip() or "软著材料"
