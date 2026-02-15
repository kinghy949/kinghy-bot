"""生成任务API"""
import logging
from datetime import date
from flask import Blueprint, request, jsonify

from config import Config
from generators.models import ProjectContext
from utils.tech_stack_loader import load_tech_stack

logger = logging.getLogger(__name__)
generate_bp = Blueprint('generate', __name__)


@generate_bp.route('/generate', methods=['POST'])
def create_generate_task():
    """提交生成任务"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400

    # 参数校验
    software_name = data.get('software_name', '').strip()
    description = data.get('description', '').strip()
    tech_stack = data.get('tech_stack', '').strip()
    target_lines = data.get('target_lines', 5000)
    completion_date = data.get('completion_date', date.today().isoformat())

    if not software_name:
        return jsonify({"error": "软著名称不能为空"}), 400
    if not description:
        return jsonify({"error": "项目描述不能为空"}), 400
    if not tech_stack:
        return jsonify({"error": "请选择技术栈"}), 400

    # 校验目标行数范围
    target_lines = max(3000, min(8000, int(target_lines)))

    # 加载技术栈配置
    tech_config = load_tech_stack(tech_stack)
    if not tech_config:
        return jsonify({"error": f"不支持的技术栈: {tech_stack}"}), 400

    # 自动提取简称（去掉"基于xxx的"前缀和"系统/平台"后缀）
    short_name = software_name
    for prefix in ['基于', '面向']:
        if short_name.startswith(prefix):
            idx = short_name.find('的')
            if idx > 0:
                short_name = short_name[idx + 1:]
            break

    # 构建项目上下文
    context = ProjectContext(
        software_name=software_name,
        short_name=short_name,
        description=description,
        tech_stack_id=tech_stack,
        tech_config=tech_config,
        target_lines=target_lines,
        completion_date=completion_date,
    )

    # 提交任务
    from app import task_manager
    from generators.orchestrator import Orchestrator

    orchestrator = Orchestrator(task_manager)
    task_id = task_manager.submit_task(orchestrator.run, context)

    return jsonify({"task_id": task_id}), 201


@generate_bp.route('/tech-stacks', methods=['GET'])
def get_tech_stacks():
    """获取可用技术栈列表"""
    from utils.tech_stack_loader import load_all_tech_stacks
    stacks = load_all_tech_stacks()
    return jsonify(stacks)
