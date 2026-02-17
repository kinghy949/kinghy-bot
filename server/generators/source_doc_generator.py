"""源码文档生成器"""
from config import Config
from generators.models import ProjectContext


class SourceDocGenerator:
    def generate(self, task_id: str, context: ProjectContext) -> str:
        try:
            from docx import Document
            from docx.shared import Cm, Pt
        except ImportError:
            return self._fallback_text(task_id, context)

        doc = Document()
        sec = doc.sections[0]
        sec.top_margin = Cm(2.54)
        sec.bottom_margin = Cm(2.54)
        sec.left_margin = Cm(3.17)
        sec.right_margin = Cm(3.17)

        sec.header.paragraphs[0].text = f"{context.software_name}源程序"
        sec.footer.paragraphs[0].text = "第X页"
        doc.add_heading(f"{context.software_name} 源程序文档", level=1)

        all_lines: list[tuple[str, str]] = []
        for path in sorted(context.generated_code.keys()):
            for line in context.generated_code[path].splitlines():
                all_lines.append((path, line))

        max_lines = 60 * 50
        if len(all_lines) > max_lines:
            half = max_lines // 2
            selected = all_lines[:half] + all_lines[-half:]
        else:
            selected = all_lines

        current_file = ""
        line_no = 1
        for file_path, line in selected:
            if file_path != current_file:
                doc.add_heading(file_path, level=2)
                current_file = file_path
                line_no = 1
            p = doc.add_paragraph(f"{line_no:04d}  {line}")
            for run in p.runs:
                run.font.name = "Courier New"
                run.font.size = Pt(10.5)
            line_no += 1

        out = Config.OUTPUT_DIR / task_id
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{self._safe(context.software_name)}_源程序.docx"
        doc.save(path)
        return str(path)

    def _fallback_text(self, task_id: str, context: ProjectContext) -> str:
        out = Config.OUTPUT_DIR / task_id
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{self._safe(context.software_name)}_源程序.txt"
        chunks = [f"{context.software_name} 源程序文档\n"]
        for file_path in sorted(context.generated_code.keys()):
            chunks.append(f"\n## {file_path}\n")
            for i, line in enumerate(context.generated_code[file_path].splitlines(), start=1):
                chunks.append(f"{i:04d} {line}\n")
        path.write_text("".join(chunks), encoding="utf-8")
        return str(path)

    def _safe(self, name: str) -> str:
        return "".join(ch if ch not in '\\/:*?\"<>|' else "_" for ch in name).strip() or "软著材料"
