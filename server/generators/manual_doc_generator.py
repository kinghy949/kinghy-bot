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

        doc.add_heading("1. 系统概述", level=1)
        doc.add_paragraph(context.description)

        doc.add_heading("2. 角色与权限说明", level=1)
        doc.add_paragraph("系统管理员：负责账号、权限、参数配置与全量数据管理。")
        doc.add_paragraph("业务操作员：负责日常业务录入、查询、更新与状态维护。")
        doc.add_paragraph("审计/访客角色：仅可查看授权范围内的数据与报表。")

        doc.add_heading("目录", level=1)
        self._insert_toc(doc)

        doc.add_heading("3. 安装与配置", level=1)
        self._write_install_sections(doc, context.tech_config)

        doc.add_heading("4. 功能操作指南", level=1)
        for i, feature in enumerate(context.feature_list, start=1):
            doc.add_heading(f"4.{i} {feature.name}", level=2)
            doc.add_paragraph(feature.description)
            doc.add_paragraph(feature.operation_steps or "进入对应模块，根据页面提示完成操作。")

            shot = feature.screenshot_path
            if shot and Path(shot).exists():
                doc.add_picture(shot, width=Inches(6.0))
                doc.add_paragraph(f"图{i} {feature.name}界面")
            else:
                doc.add_paragraph("截图缺失，请后续补充真实截图。")

        doc.add_heading("5. 注意事项", level=1)
        doc.add_heading("5.1 常见问题", level=2)
        doc.add_paragraph("若页面无数据，请检查筛选条件、权限范围与后端服务连接状态。")
        doc.add_paragraph("若导出失败，请检查磁盘空间、目录权限与目标文件是否被占用。")
        doc.add_heading("5.2 运维建议", level=2)
        doc.add_paragraph("建议每日备份数据库并保留至少7天快照；关键日志至少保留30天。")
        doc.add_paragraph("建议按周检查任务执行告警、截图生成失败率与文档输出完整性。")

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
        lines.append("3. 安装与配置\n")
        lines.append(f"3.1 环境准备：{context.tech_config.get('runtime', '见部署说明')}\n")
        lines.append("3.2 部署步骤：\n")
        install_steps = str(context.tech_config.get("install_steps", "")).strip() or "请按技术栈说明完成安装。"
        lines.append(f"{install_steps}\n")
        lines.append("3.3 启动与验证：启动服务后访问首页并检查核心功能页面可正常打开。\n\n")
        for i, feature in enumerate(context.feature_list, start=1):
            lines.append(f"{i}. {feature.name}\n")
            lines.append(f"说明：{feature.description}\n")
            lines.append(f"步骤：{feature.operation_steps or '进入页面执行操作'}\n")
            lines.append(f"截图：{feature.screenshot_path or '无'}\n\n")
        lines.append("5. 注意事项\n")
        lines.append("5.1 常见问题：若无数据请检查权限和筛选条件。\n")
        lines.append("5.2 运维建议：定期备份数据库并检查任务日志。\n")
        path.write_text("".join(lines), encoding="utf-8")
        return str(path)

    def _write_install_sections(self, doc, tech_config: dict):
        doc.add_heading("3.1 环境准备", level=2)
        doc.add_paragraph(f"软件环境：{tech_config.get('runtime', '见部署说明')}")
        doc.add_paragraph(f"开发工具：{tech_config.get('dev_tools', '见部署说明')}")
        doc.add_paragraph(f"操作系统：{tech_config.get('os', 'Windows/Linux')}")

        doc.add_heading("3.2 部署步骤", level=2)
        steps = str(tech_config.get("install_steps", "")).strip()
        if steps:
            for line in [s.strip() for s in steps.splitlines() if s.strip()]:
                doc.add_paragraph(line)
        else:
            doc.add_paragraph("请根据技术栈完成依赖安装、服务启动与环境变量配置。")

        doc.add_heading("3.3 启动与验证", level=2)
        doc.add_paragraph("完成部署后，启动后端与前端服务。")
        doc.add_paragraph("访问系统首页，验证登录、列表、表单、详情、统计页面可正常使用。")

    def _insert_toc(self, doc):
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        p = doc.add_paragraph()
        r = p.add_run()
        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = 'TOC \\o "1-3" \\h \\z \\u'
        separate = OxmlElement("w:fldChar")
        separate.set(qn("w:fldCharType"), "separate")
        text = OxmlElement("w:t")
        text.text = "目录（在 Word 中右键“更新域”刷新）"
        separate.append(text)
        end = OxmlElement("w:fldChar")
        end.set(qn("w:fldCharType"), "end")
        r._r.append(begin)
        r._r.append(instr)
        r._r.append(separate)
        r._r.append(end)

    def _safe(self, name: str) -> str:
        return "".join(ch if ch not in '\\/:*?\"<>|' else "_" for ch in name).strip() or "软著材料"
