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
    logger.info("接口入参 /download/%s/%s: 请求下载单文件", task_id, doc_type)
    from app import task_manager
    state = task_manager.get_task_state(task_id)
    if not state:
        resp = {"error": "任务不存在"}
        logger.warning("接口出参 /download/%s/%s: status=404, body=%s", task_id, doc_type, resp)
        return jsonify(resp), 404
    if state['status'] != 'completed':
        resp = {"error": "任务尚未完成"}
        logger.warning("接口出参 /download/%s/%s: status=400, body=%s", task_id, doc_type, resp)
        return jsonify(resp), 400

    output_files = state.get('output_files', {})
    if doc_type not in output_files:
        resp = {"error": f"文档类型 {doc_type} 不存在"}
        logger.warning("接口出参 /download/%s/%s: status=404, body=%s", task_id, doc_type, resp)
        return jsonify(resp), 404

    filepath = Path(output_files[doc_type])
    if not filepath.exists():
        resp = {"error": "文件不存在，可能已过期清理"}
        logger.warning("接口出参 /download/%s/%s: status=404, body=%s", task_id, doc_type, resp)
        return jsonify(resp), 404

    logger.info("接口出参 /download/%s/%s: status=200, filename=%s", task_id, doc_type, filepath.name)

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filepath.name,
    )


@download_bp.route('/download/<task_id>/all', methods=['GET'])
def download_all(task_id):
    """下载ZIP包（3个文档）"""
    logger.info("接口入参 /download/%s/all: 请求下载ZIP", task_id)
    from app import task_manager
    state = task_manager.get_task_state(task_id)
    if not state:
        resp = {"error": "任务不存在"}
        logger.warning("接口出参 /download/%s/all: status=404, body=%s", task_id, resp)
        return jsonify(resp), 404
    if state['status'] != 'completed':
        resp = {"error": "任务尚未完成"}
        logger.warning("接口出参 /download/%s/all: status=400, body=%s", task_id, resp)
        return jsonify(resp), 400

    output_files = state.get('output_files', {})
    if not output_files:
        resp = {"error": "没有可下载的文件"}
        logger.warning("接口出参 /download/%s/all: status=404, body=%s", task_id, resp)
        return jsonify(resp), 404

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
    logger.info(
        "接口出参 /download/%s/all: status=200, zip_name=%s_软著材料.zip, file_count=%s",
        task_id,
        software_name,
        len(output_files),
    )
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{software_name}_软著材料.zip',
    )
