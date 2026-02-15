"""文件下载API"""
import logging
import zipfile
from io import BytesIO
from pathlib import Path
from flask import Blueprint, send_file, jsonify

from config import Config

logger = logging.getLogger(__name__)
download_bp = Blueprint('download', __name__)

# 文档类型映射
DOC_TYPES = {
    'source': '源程序',
    'manual': '操作手册',
    'application': '申请表',
}


@download_bp.route('/download/<task_id>/<doc_type>', methods=['GET'])
def download_file(task_id, doc_type):
    """下载单个文档"""
    from app import task_manager
    state = task_manager.get_task_state(task_id)
    if not state:
        return jsonify({"error": "任务不存在"}), 404
    if state['status'] != 'completed':
        return jsonify({"error": "任务尚未完成"}), 400

    output_files = state.get('output_files', {})
    if doc_type not in output_files:
        return jsonify({"error": f"文档类型 {doc_type} 不存在"}), 404

    filepath = Path(output_files[doc_type])
    if not filepath.exists():
        return jsonify({"error": "文件不存在，可能已过期清理"}), 404

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filepath.name,
    )


@download_bp.route('/download/<task_id>/all', methods=['GET'])
def download_all(task_id):
    """下载ZIP包（3个文档）"""
    from app import task_manager
    state = task_manager.get_task_state(task_id)
    if not state:
        return jsonify({"error": "任务不存在"}), 404
    if state['status'] != 'completed':
        return jsonify({"error": "任务尚未完成"}), 400

    output_files = state.get('output_files', {})
    if not output_files:
        return jsonify({"error": "没有可下载的文件"}), 404

    # 获取软著名称用于ZIP文件名
    software_name = state.get('context', {}).get('software_name', '软著材料')

    # 创建内存ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for doc_type, filepath_str in output_files.items():
            filepath = Path(filepath_str)
            if filepath.exists():
                zf.write(filepath, filepath.name)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{software_name}_软著材料.zip',
    )
