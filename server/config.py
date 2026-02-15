"""Flask应用配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent


class Config:
    """应用配置"""

    # AI模型配置
    AI_PRIMARY_PROVIDER = os.getenv('AI_PRIMARY_PROVIDER', 'zhipu')
    AI_PRIMARY_API_KEY = os.getenv('AI_PRIMARY_API_KEY', '')
    AI_PRIMARY_MODEL = os.getenv('AI_PRIMARY_MODEL', 'glm-4')

    AI_FALLBACK_PROVIDER = os.getenv('AI_FALLBACK_PROVIDER', '')
    AI_FALLBACK_API_KEY = os.getenv('AI_FALLBACK_API_KEY', '')
    AI_FALLBACK_MODEL = os.getenv('AI_FALLBACK_MODEL', '')

    # 文件存储路径
    OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', str(BASE_DIR / 'output')))
    SCREENSHOT_DIR = Path(os.getenv('SCREENSHOT_DIR', str(BASE_DIR / 'screenshots')))
    TASK_DATA_DIR = Path(os.getenv('TASK_DATA_DIR', str(BASE_DIR / 'data' / 'tasks')))

    # 任务配置
    MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', '2'))
    FILE_RETENTION_HOURS = int(os.getenv('FILE_RETENTION_HOURS', '24'))

    # 技术栈配置目录
    TECH_STACKS_DIR = BASE_DIR / 'tech_stacks'
    CODE_TEMPLATES_DIR = BASE_DIR / 'code_templates'
    HTML_TEMPLATES_DIR = BASE_DIR / 'html_templates'
    TEMPLATE_DIR = BASE_DIR / 'template'

    # 提示词模板目录
    PROMPTS_DIR = BASE_DIR / 'ai' / 'prompts'
