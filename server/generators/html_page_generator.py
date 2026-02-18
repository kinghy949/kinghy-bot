"""HTML页面生成器"""
import html
import json
import re

from ai.prompt_builder import build_page_prompt
from config import Config
from generators.models import ProjectContext


class HtmlPageGenerator:
    def __init__(self):
        self.ai_client = None

    def generate(self, task_id: str, context: ProjectContext) -> dict[str, str]:
        output: dict[str, str] = {}
        base_dir = Config.OUTPUT_DIR / task_id / "work" / "html"
        base_dir.mkdir(parents=True, exist_ok=True)

        for idx, feature in enumerate(context.feature_list, start=1):
            filename = f"{idx:02d}_{self._slug(feature.name)}.html"
            path = base_dir / filename
            page_payload = self._build_page_payload(feature.name, feature.description, feature.page_type)
            html_page = self._build_page(
                software_name=context.software_name,
                page_type=feature.page_type,
                payload=page_payload,
            )
            path.write_text(html_page, encoding="utf-8")
            output[feature.name] = str(path)
            feature.html_path = str(path)

        context.generated_html_pages = output
        return output

    def _build_page(self, software_name: str, page_type: str, payload: dict) -> str:
        template = self._load_template(page_type)
        rendered = template
        rendered = rendered.replace("{{software_name}}", html.escape(software_name))
        rendered = rendered.replace("{{title}}", html.escape(str(payload.get("title", ""))))
        rendered = rendered.replace("{{subtitle}}", html.escape(str(payload.get("subtitle", ""))))
        rendered = rendered.replace("{{menus_html}}", self._render_menus(payload.get("menus", [])))
        rendered = rendered.replace("{{fields_html}}", self._render_fields(payload.get("fields", [])))
        rendered = rendered.replace("{{table_head_html}}", self._render_table_head(payload.get("table_columns", [])))
        rendered = rendered.replace("{{table_rows_html}}", self._render_table_rows(payload.get("table_columns", []), payload.get("sample_rows", [])))
        rendered = rendered.replace("{{chart_title}}", html.escape(str(payload.get("chart_title", ""))))
        rendered = rendered.replace("{{chart_summary}}", html.escape(str(payload.get("chart_summary", ""))))
        return rendered

    def _build_page_payload(self, feature_name: str, feature_desc: str, page_type: str) -> dict:
        prompt = build_page_prompt(feature_name, feature_desc, page_type)
        try:
            if self.ai_client is None:
                from ai.ai_client import AIClient

                self.ai_client = AIClient()
            raw = self.ai_client.generate(prompt, max_retries=1)
            return self._parse_payload(raw, feature_name, feature_desc)
        except Exception:
            return self._fallback_payload(feature_name, feature_desc)

    def _parse_payload(self, raw: str, feature_name: str, feature_desc: str) -> dict:
        text = raw.strip()
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            text = match.group(0)
        data = json.loads(text)
        if not isinstance(data, dict):
            return self._fallback_payload(feature_name, feature_desc)
        fallback = self._fallback_payload(feature_name, feature_desc)
        fallback.update(data)
        return fallback

    def _fallback_payload(self, feature_name: str, feature_desc: str) -> dict:
        return {
            "title": feature_name,
            "subtitle": feature_desc,
            "menus": ["首页", "业务管理", "统计分析"],
            "fields": [
                {"name": "name", "label": "名称", "type": "text"},
                {"name": "status", "label": "状态", "type": "select"},
                {"name": "owner", "label": "负责人", "type": "text"},
                {"name": "updated_at", "label": "更新时间", "type": "date"},
            ],
            "table_columns": ["编号", "名称", "状态"],
            "sample_rows": [
                {"编号": "1", "名称": f"{feature_name}样例A", "状态": "启用"},
                {"编号": "2", "名称": f"{feature_name}样例B", "状态": "停用"},
                {"编号": "3", "名称": f"{feature_name}样例C", "状态": "启用"},
            ],
            "chart_title": f"{feature_name}趋势",
            "chart_summary": "近三个月整体指标稳定增长。",
        }

    def _load_template(self, page_type: str) -> str:
        path = Config.HTML_TEMPLATES_DIR / f"{page_type}.html"
        if path.exists():
            return path.read_text(encoding="utf-8")
        fallback = Config.HTML_TEMPLATES_DIR / "list.html"
        if fallback.exists():
            return fallback.read_text(encoding="utf-8")
        return "<html><body><h1>{{title}}</h1><p>{{subtitle}}</p></body></html>"

    def _render_menus(self, menus: list) -> str:
        return "\n".join(f"<li>{html.escape(str(item))}</li>" for item in menus[:8])

    def _render_fields(self, fields: list) -> str:
        html_fields = []
        for field in fields[:12]:
            label = html.escape(str(field.get("label", field.get("name", "字段"))))
            html_fields.append(
                f"<div class='field'><label>{label}</label><input placeholder='请输入{label}' /></div>"
            )
        return "\n".join(html_fields)

    def _render_table_head(self, columns: list) -> str:
        return "".join(f"<th>{html.escape(str(c))}</th>" for c in columns[:10])

    def _render_table_rows(self, columns: list, rows: list) -> str:
        html_rows = []
        safe_columns = [str(c) for c in columns[:10]]
        for row in rows[:20]:
            cells = "".join(f"<td>{html.escape(str(row.get(c, '')))}</td>" for c in safe_columns)
            html_rows.append(f"<tr>{cells}</tr>")
        return "\n".join(html_rows)

    def _slug(self, text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", text).strip("_").lower() or "feature"
