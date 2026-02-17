"""申请表生成器 - MVP版"""
from config import Config
from generators.models import ProjectContext


class ApplicationDocGenerator:
    MANUAL_FIELDS = ["著作权人", "证件号码", "联系地址", "联系电话", "权利取得方式", "权利范围"]

    def generate(self, task_id: str, context: ProjectContext) -> str:
        try:
            from docx import Document
            from docx.enum.text import WD_COLOR_INDEX
        except ImportError:
            return self._fallback_text(task_id, context)

        doc = Document()
        doc.add_heading("计算机软件著作权登记申请表（自动生成草稿）", level=1)
        table = doc.add_table(rows=0, cols=2)
        rows = [
            ("软件全称", context.software_name),
            ("软件简称", context.short_name),
            ("版本号", "V1.0"),
            ("开发完成日期", context.completion_date),
            ("源程序量", str(context.total_lines)),
            ("编程语言", context.tech_config.get("languages", "")),
            ("主要功能", context.feature_summary),
            ("运行环境", context.tech_config.get("os", "")),
            ("软件环境", context.tech_config.get("runtime", "")),
            ("开发工具", context.tech_config.get("dev_tools", "")),
        ]
        for key, value in rows:
            cells = table.add_row().cells
            cells[0].text = key
            cells[1].text = value

        p = doc.add_paragraph("\n以下字段请手动填写：")
        for field in self.MANUAL_FIELDS:
            run = p.add_run(f"\n- {field}")
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW

        out = Config.OUTPUT_DIR / task_id
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{self._safe(context.software_name)}_申请表.docx"
        doc.save(path)
        return str(path)

    def _fallback_text(self, task_id: str, context: ProjectContext) -> str:
        out = Config.OUTPUT_DIR / task_id
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{self._safe(context.software_name)}_申请表.txt"
        text = [
            "计算机软件著作权登记申请表（自动生成草稿）\n\n",
            f"软件全称：{context.software_name}\n",
            f"软件简称：{context.short_name}\n",
            "版本号：V1.0\n",
            f"开发完成日期：{context.completion_date}\n",
            f"源程序量：{context.total_lines}\n",
            f"编程语言：{context.tech_config.get('languages', '')}\n",
            f"主要功能：{context.feature_summary}\n\n",
            "以下字段需手动填写：\n",
        ]
        text.extend([f"- {f}\n" for f in self.MANUAL_FIELDS])
        path.write_text("".join(text), encoding="utf-8")
        return str(path)

    def _safe(self, name: str) -> str:
        return "".join(ch if ch not in '\\/:*?\"<>|' else "_" for ch in name).strip() or "软著材料"
