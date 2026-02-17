"""HTML页面生成器"""
import html
import re
from pathlib import Path

from config import Config
from generators.models import ProjectContext


class HtmlPageGenerator:
    def generate(self, task_id: str, context: ProjectContext) -> dict[str, str]:
        output: dict[str, str] = {}
        base_dir = Config.OUTPUT_DIR / task_id / "work" / "html"
        base_dir.mkdir(parents=True, exist_ok=True)

        for idx, feature in enumerate(context.feature_list, start=1):
            filename = f"{idx:02d}_{self._slug(feature.name)}.html"
            path = base_dir / filename
            path.write_text(self._build_page(context.software_name, feature.name, feature.description, feature.page_type), encoding="utf-8")
            output[feature.name] = str(path)
            feature.html_path = str(path)

        context.generated_html_pages = output
        return output

    def _build_page(self, software_name: str, feature_name: str, feature_desc: str, page_type: str) -> str:
        title = html.escape(feature_name)
        desc = html.escape(feature_desc)
        software = html.escape(software_name)
        body = self._page_fragment(page_type, title)
        return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
    body {{ margin: 0; background: #f3f5f7; color: #303133; }}
    .layout {{ display: flex; min-height: 100vh; }}
    .sidebar {{ width: 220px; background: #1f2d3d; color: #dbe3ee; padding: 20px; }}
    .sidebar h3 {{ color: #fff; margin-top: 0; font-size: 16px; }}
    .sidebar li {{ margin: 10px 0; font-size: 13px; }}
    .content {{ flex: 1; padding: 24px; }}
    .panel {{ background: #fff; border-radius: 10px; padding: 18px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }}
    .title {{ font-size: 22px; margin: 0 0 8px; }}
    .sub {{ color: #606266; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border: 1px solid #ebeef5; padding: 10px; text-align: left; font-size: 13px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
    .stat {{ background: #f7fbff; border: 1px solid #d9ecff; padding: 14px; border-radius: 8px; }}
    .btn {{ background: #409eff; color: #fff; border: 0; padding: 8px 16px; border-radius: 6px; }}
    .field {{ margin: 10px 0; }}
    .field label {{ display: block; color: #606266; margin-bottom: 4px; font-size: 12px; }}
    .field input {{ width: 100%; border: 1px solid #dcdfe6; border-radius: 6px; padding: 8px; }}
  </style>
</head>
<body>
  <div class=\"layout\">
    <aside class=\"sidebar\">
      <h3>{software}</h3>
      <ul>
        <li>首页</li>
        <li>基础管理</li>
        <li>业务管理</li>
        <li>统计分析</li>
      </ul>
    </aside>
    <main class=\"content\">
      <section class=\"panel\">
        <h1 class=\"title\">{title}</h1>
        <div class=\"sub\">{desc}</div>
        {body}
      </section>
    </main>
  </div>
</body>
</html>
"""

    def _page_fragment(self, page_type: str, title: str) -> str:
        if page_type == "login":
            return (
                "<div style='max-width:360px'>"
                "<div class='field'><label>用户名</label><input value='admin' /></div>"
                "<div class='field'><label>密码</label><input value='******' /></div>"
                "<button class='btn'>登录系统</button></div>"
            )
        if page_type == "dashboard":
            return (
                "<div class='grid'>"
                "<div class='stat'><strong>128</strong><div>今日新增</div></div>"
                "<div class='stat'><strong>96%</strong><div>任务完成率</div></div>"
                "<div class='stat'><strong>36</strong><div>待处理事项</div></div>"
                "</div>"
            )
        if page_type == "form":
            return (
                "<div style='max-width:520px'>"
                "<div class='field'><label>名称</label><input value='示例数据' /></div>"
                "<div class='field'><label>状态</label><input value='启用' /></div>"
                "<div class='field'><label>备注</label><input value='系统自动生成示例' /></div>"
                "<button class='btn'>保存</button></div>"
            )
        if page_type == "detail":
            return (
                "<table><tr><th>字段</th><th>值</th></tr>"
                f"<tr><td>模块名称</td><td>{title}</td></tr>"
                "<tr><td>创建人</td><td>管理员</td></tr>"
                "<tr><td>更新时间</td><td>2026-02-17</td></tr></table>"
            )
        if page_type == "chart":
            return (
                "<div class='grid'>"
                "<div class='stat'><strong>Q1</strong><div>业务增长 12%</div></div>"
                "<div class='stat'><strong>Q2</strong><div>业务增长 18%</div></div>"
                "<div class='stat'><strong>Q3</strong><div>业务增长 21%</div></div>"
                "</div>"
            )
        return (
            "<table><tr><th>ID</th><th>名称</th><th>状态</th></tr>"
            "<tr><td>1</td><td>示例一</td><td>启用</td></tr>"
            "<tr><td>2</td><td>示例二</td><td>停用</td></tr>"
            "<tr><td>3</td><td>示例三</td><td>启用</td></tr></table>"
        )

    def _slug(self, text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", text).strip("_").lower() or "feature"
