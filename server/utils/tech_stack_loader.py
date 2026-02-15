"""技术栈配置加载器"""
import logging
from pathlib import Path
import yaml

from config import Config

logger = logging.getLogger(__name__)


def load_tech_stack(stack_id: str) -> dict | None:
    """加载指定技术栈的YAML配置"""
    config_path = Config.TECH_STACKS_DIR / f"{stack_id}.yaml"
    if not config_path.exists():
        logger.error(f"技术栈配置文件不存在: {config_path}")
        return None
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载技术栈配置失败: {e}")
        return None


def load_all_tech_stacks() -> list[dict]:
    """加载所有可用技术栈列表（用于前端下拉选项）"""
    stacks = []
    if not Config.TECH_STACKS_DIR.exists():
        return stacks
    for config_path in sorted(Config.TECH_STACKS_DIR.glob("*.yaml")):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                stacks.append({
                    'id': data.get('id', config_path.stem),
                    'name': data.get('name', config_path.stem),
                    'description': data.get('description', ''),
                })
        except Exception as e:
            logger.error(f"加载技术栈 {config_path.name} 失败: {e}")
    return stacks
