"""提示词构建器。"""

from config import Config


def _load_prompt_template(filename: str, fallback: str) -> str:
    path = Config.PROMPTS_DIR / filename
    try:
        text = path.read_text(encoding="utf-8").strip()
        return text or fallback
    except Exception:
        return fallback


def _fill_template(template: str, mapping: dict[str, str]) -> str:
    result = template
    for key, value in mapping.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


def build_feature_prompt(software_name: str, description: str) -> str:
    template = _load_prompt_template(
        "feature_gen.txt",
        "请输出6个功能模块JSON数组，每项包含name/description/page_type/operation_steps。",
    )
    return _fill_template(
        template,
        {
            "software_name": software_name,
            "description": description,
        },
    )


def build_code_prompt(feature: dict, tech_stack: dict, existing_files: list[str]) -> str:
    template = _load_prompt_template(
        "code_gen.txt",
        (
            "请为功能生成代码，输出JSON对象，包含files数组，每项有path/purpose/content。"
            "输入：{feature_name} {feature_description} {tech_stack} {existing_files}"
        ),
    )
    return _fill_template(
        template,
        {
            "feature_name": feature.get("name", ""),
            "feature_description": feature.get("description", ""),
            "tech_stack": tech_stack.get("name", tech_stack.get("id", "")),
            "existing_files": "\n".join(existing_files),
        },
    )


def build_manual_prompt(software_name: str, description: str, tech_config: dict, features: list[dict]) -> str:
    template = _load_prompt_template(
        "manual_gen.txt",
        "请生成操作手册正文，包含系统概述、安装配置、功能操作、注意事项。",
    )
    return _fill_template(
        template,
        {
            "software_name": software_name,
            "description": description,
            "tech_config": str(tech_config),
            "features": str(features),
        },
    )


def build_page_prompt(feature_name: str, feature_description: str, page_type: str) -> str:
    template = _load_prompt_template(
        "page_gen.txt",
        "请输出页面内容JSON，包含title/subtitle/menus/fields/table_columns/sample_rows/chart_title/chart_summary。",
    )
    return _fill_template(
        template,
        {
            "feature_name": feature_name,
            "feature_description": feature_description,
            "page_type": page_type,
        },
    )
