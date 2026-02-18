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
        self._set_page_footer(sec.footer.paragraphs[0])
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

    def _set_page_footer(self, paragraph):
        paragraph.clear()
        paragraph.add_run("第 ")
        self._add_field(paragraph, "PAGE")
        paragraph.add_run(" 页 共 ")
        self._add_field(paragraph, "NUMPAGES")
        paragraph.add_run(" 页")

    def _add_field(self, paragraph, field_name: str):
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        run = paragraph.add_run()
        fld_char_begin = OxmlElement("w:fldChar")
        fld_char_begin.set(qn("w:fldCharType"), "begin")
        instr_text = OxmlElement("w:instrText")
        instr_text.set(qn("xml:space"), "preserve")
        instr_text.text = field_name
        fld_char_end = OxmlElement("w:fldChar")
        fld_char_end.set(qn("w:fldCharType"), "end")
        run._r.append(fld_char_begin)
        run._r.append(instr_text)
        run._r.append(fld_char_end)

    def _safe(self, name: str) -> str:
        return "".join(ch if ch not in '\\/:*?\"<>|' else "_" for ch in name).strip() or "软著材料"
