"""混合代码生成器 - MVP版本（模板骨架 + 自动扩展）"""
import json
import logging
import re
from pathlib import Path

from ai.prompt_builder import build_code_prompt
from config import BASE_DIR, Config
from generators.code_checker import CodeChecker
from generators.models import ProjectContext

logger = logging.getLogger(__name__)


class CodeGenerator:
    def __init__(self):
        self.checker = CodeChecker()
        self.ai_client = None

    def generate(self, task_id: str, context: ProjectContext) -> dict[str, str]:
        code: dict[str, str] = {}

        code.update(self._base_files(context))
        for feature in context.feature_list:
            existing_files = list(code.keys())
            feature_files = self._feature_files_by_ai(context, feature.name, feature.description, existing_files)
            if not feature_files:
                feature_files = self._feature_files(context, feature.name)
            feature.code_files = list(feature_files.keys())
            code.update(feature_files)

        code = self._expand_to_target(code, context.target_lines)

        stats = self.checker.check(code, context.target_lines)
        context.total_lines = stats.total_lines
        context.generated_code = code

        self._persist_code(task_id, code)
        return code

    def _base_files(self, context: ProjectContext) -> dict[str, str]:
        files = self._base_files_from_templates(context)
        if files:
            return files
        return self._base_files_fallback(context)

    def _base_files_from_templates(self, context: ProjectContext) -> dict[str, str]:
        template_dir = self._resolve_template_dir(context)
        if not template_dir.exists():
            logger.warning("代码模板目录不存在，使用降级骨架: %s", template_dir)
            return {}

        template_files = [p for p in template_dir.rglob("*") if p.is_file()]
        if not template_files:
            logger.warning("代码模板目录为空，使用降级骨架: %s", template_dir)
            return {}

        replacements = {
            "SOFTWARE_NAME": context.software_name,
            "DESCRIPTION": context.description,
            "TECH_STACK_NAME": context.tech_config.get("name", context.tech_stack_id),
        }
        output: dict[str, str] = {}
        for file in template_files:
            rel = file.relative_to(template_dir).as_posix()
            out_path = rel[:-4] if rel.endswith(".tpl") else rel
            content = file.read_text(encoding="utf-8")
            output[out_path] = self._render_tokens(content, replacements)
        return output

    def _base_files_fallback(self, context: ProjectContext) -> dict[str, str]:
        name = context.software_name
        stack = context.tech_stack_id
        files: dict[str, str] = {
            "README.md": (
                f"# {name}\n\n"
                f"## 项目简介\n{context.description}\n\n"
                "## 主要功能\n"
                + "\n".join([f"- {f.name}：{f.description}" for f in context.feature_list])
                + "\n"
            ),
            "docs/architecture.md": (
                "# 系统架构说明\n\n"
                f"技术栈：{context.tech_config.get('name', stack)}\n\n"
                "系统采用前后端分离架构，后端提供REST API，前端提供管理界面。\n"
            ),
            "frontend/src/main.js": (
                "import { createApp } from 'vue'\n"
                "import App from './App.vue'\n"
                "createApp(App).mount('#app')\n"
            ),
            "frontend/src/App.vue": (
                "<template>\n"
                "  <div class=\"app\">\n"
                f"    <h1>{name}</h1>\n"
                "  </div>\n"
                "</template>\n"
            ),
        }
        if stack == "springboot_vue":
            files["backend/src/main/java/com/example/Application.java"] = (
                "package com.example;\n\n"
                "public class Application {\n"
                "    public static void main(String[] args) {\n"
                "        System.out.println(\"Application started\");\n"
                "    }\n"
                "}\n"
            )
        else:
            files["backend/app.py"] = (
                "\"\"应用入口\"\"\"\n"
                "def create_app():\n"
                "    app_name = 'demo-app'\n"
                "    return app_name\n\n"
                "if __name__ == '__main__':\n"
                "    print(create_app())\n"
            )
        return files

    def _feature_files(self, context: ProjectContext, feature_name: str) -> dict[str, str]:
        slug = self._slug(feature_name)
        files: dict[str, str] = {}

        if context.tech_stack_id == "springboot_vue":
            files[f"backend/src/main/java/com/example/modules/{slug}/{self._camel(slug)}Service.java"] = self._java_service(feature_name)
            files[f"backend/src/main/java/com/example/modules/{slug}/{self._camel(slug)}Controller.java"] = self._java_controller(feature_name)
        else:
            files[f"backend/modules/{slug}_service.py"] = self._py_service(feature_name)
            files[f"backend/modules/{slug}_controller.py"] = self._py_controller(feature_name)

        files[f"frontend/src/views/{self._camel(slug)}View.vue"] = self._vue_view(feature_name)
        files[f"frontend/src/api/{slug}.js"] = self._js_api(feature_name)
        return files

    def _feature_files_by_ai(
        self,
        context: ProjectContext,
        feature_name: str,
        feature_desc: str,
        existing_files: list[str],
    ) -> dict[str, str]:
        logger.info("触发功能代码生成: feature=%s", feature_name)
        prompt = build_code_prompt(
            feature={"name": feature_name, "description": feature_desc},
            tech_stack=context.tech_config,
            existing_files=existing_files,
        )
        try:
            if self.ai_client is None:
                from ai.ai_client import AIClient

                self.ai_client = AIClient()
            raw = self.ai_client.generate(prompt, max_retries=1)
            return self._parse_ai_files(raw, existing_files)
        except Exception as e:
            logger.warning("AI功能代码生成失败，使用兜底模板: feature=%s, err=%s", feature_name, e)
            return {}

    def _parse_ai_files(self, raw: str, existing_files: list[str]) -> dict[str, str]:
        text = raw.strip()
        object_match = re.search(r"\{[\s\S]*\}", text)
        if object_match:
            text = object_match.group(0)
        data = json.loads(text)
        files = data.get("files", [])
        if not isinstance(files, list):
            return {}

        existed = set(existing_files)
        result: dict[str, str] = {}
        for item in files:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path", "")).strip().lstrip("./")
            content = str(item.get("content", ""))
            if not path or not content:
                continue
            if path in existed or path in result:
                continue
            result[path] = content
        return result

    def _expand_to_target(self, code: dict[str, str], target_lines: int) -> dict[str, str]:
        current = sum(c.count("\n") + 1 for c in code.values())
        min_lines = int(target_lines * 0.8)
        if current >= min_lines:
            return code

        deficit = min_lines - current
        chunk = 120
        index = 1
        while deficit > 0:
            lines = min(chunk, deficit)
            content = ["# 自动补充实现说明"]
            content.extend([f"- 扩展说明第{i}行：用于完善业务实现细节与说明。" for i in range(1, lines)])
            code[f"docs/implementation_notes/part_{index}.md"] = "\n".join(content) + "\n"
            deficit -= lines
            index += 1
        return code

    def _resolve_template_dir(self, context: ProjectContext) -> Path:
        configured = str(context.tech_config.get("code_templates_dir", "")).strip()
        if configured:
            cfg_path = Path(configured)
            if cfg_path.is_absolute():
                return cfg_path
            return BASE_DIR / cfg_path
        return Config.CODE_TEMPLATES_DIR / context.tech_stack_id

    def _render_tokens(self, text: str, replacements: dict[str, str]) -> str:
        rendered = text
        for key, value in replacements.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered

    def _persist_code(self, task_id: str, generated_code: dict[str, str]):
        base = Config.OUTPUT_DIR / task_id / "work" / "code"
        for path, content in generated_code.items():
            out = base / path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")

    def _slug(self, text: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", text).strip("_")
        if not cleaned:
            return "feature"
        return cleaned.lower()

    def _camel(self, text: str) -> str:
        parts = [p for p in re.split(r"[_\-\s]+", text) if p]
        if not parts:
            return "Feature"
        return "".join(p[:1].upper() + p[1:] for p in parts)

    def _java_service(self, feature_name: str) -> str:
        return (
            "package com.example.modules;\n\n"
            f"public class {self._camel(self._slug(feature_name))}Service {{\n"
            f"    // {feature_name} 业务服务\n"
            "    public String getSummary() {\n"
            f"        return \"{feature_name}服务运行正常\";\n"
            "    }\n"
            "}\n"
        )

    def _java_controller(self, feature_name: str) -> str:
        cname = self._camel(self._slug(feature_name))
        return (
            "package com.example.modules;\n\n"
            f"public class {cname}Controller {{\n"
            f"    private final {cname}Service service = new {cname}Service();\n\n"
            "    public String detail() {\n"
            "        return service.getSummary();\n"
            "    }\n"
            "}\n"
        )

    def _py_service(self, feature_name: str) -> str:
        return (
            f"\"\"{feature_name} 业务服务\"\"\"\n\n"
            "class FeatureService:\n"
            "    def summary(self) -> str:\n"
            f"        return \"{feature_name}服务运行正常\"\n"
        )

    def _py_controller(self, feature_name: str) -> str:
        return (
            f"\"\"{feature_name} 控制器\"\"\"\n\n"
            "from ." + self._slug(feature_name) + "_service import FeatureService\n\n"
            "service = FeatureService()\n\n"
            "def get_detail() -> dict:\n"
            "    return {\"message\": service.summary()}\n"
        )

    def _vue_view(self, feature_name: str) -> str:
        return (
            "<template>\n"
            "  <div class=\"page\">\n"
            f"    <h2>{feature_name}</h2>\n"
            "    <p>该页面用于展示和处理业务数据。</p>\n"
            "  </div>\n"
            "</template>\n\n"
            "<script setup>\n"
            "// 页面逻辑可按需扩展\n"
            "</script>\n"
        )

    def _js_api(self, feature_name: str) -> str:
        return (
            "import request from './request'\n\n"
            f"export function fetch{self._camel(self._slug(feature_name))}List(params) {{\n"
            "  return request.get('/api/list', { params })\n"
            "}\n"
        )
