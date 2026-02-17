"""技术栈配置加载器"""
import logging

from config import Config

logger = logging.getLogger(__name__)

try:
    import yaml
except ImportError:
    yaml = None


def _fallback_parse_yaml(text: str) -> dict:
    data: dict = {}
    env: dict = {}
    current = data
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.strip().startswith("#"):
            continue
        if line.startswith("environment:"):
            data["environment"] = env
            current = env
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        current[key] = value
    return data


def _load_yaml(path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
        if yaml:
            return yaml.safe_load(text)
        return _fallback_parse_yaml(text)
    except Exception as e:
        logger.error("加载YAML失败: %s", e)
        return None


def load_tech_stack(stack_id: str) -> dict | None:
    """加载指定技术栈的YAML配置"""
    config_path = Config.TECH_STACKS_DIR / f"{stack_id}.yaml"
    if not config_path.exists():
        logger.error(f"技术栈配置文件不存在: {config_path}")
        return None
    return _load_yaml(config_path)


def load_all_tech_stacks() -> list[dict]:
    """加载所有可用技术栈列表（用于前端下拉选项）"""
    stacks = []
    if not Config.TECH_STACKS_DIR.exists():
        return stacks
    for config_path in sorted(Config.TECH_STACKS_DIR.glob("*.yaml")):
        data = _load_yaml(config_path)
        if not data:
            continue
        stacks.append(
            {
                "id": data.get("id", config_path.stem),
                "name": data.get("name", config_path.stem),
                "description": data.get("description", ""),
            }
        )
    return stacks
