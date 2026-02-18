"""任务状态API + SSE进度推送"""
import json
import time
import logging
from flask import Blueprint, Response, jsonify

logger = logging.getLogger(__name__)
task_bp = Blueprint('task', __name__)


@task_bp.route('/task/<task_id>', methods=['GET'])
def get_task_state(task_id):
    """查询任务状态"""
    logger.info("接口入参 /task/%s: 无", task_id)
    from app import task_manager
    state = task_manager.get_task_state(task_id)
    if not state:
        resp = {"error": "任务不存在"}
        logger.warning("接口出参 /task/%s: status=404, body=%s", task_id, resp)
        return jsonify(resp), 404
    # 返回时排除context中的大字段（generated_code等）
    safe_state = {k: v for k, v in state.items() if k != 'context'}
    logger.info(
        "接口出参 /task/%s: status=200, task_status=%s, progress=%s",
        task_id,
        safe_state.get("status"),
        safe_state.get("progress"),
    )
    return jsonify(safe_state)


@task_bp.route('/task/<task_id>/stream', methods=['GET'])
def task_stream(task_id):
    """SSE实时进度推送"""
    logger.info("接口入参 /task/%s/stream: 建立SSE连接", task_id)
    from app import task_manager

    def event_stream():
        while True:
            state = task_manager.get_task_state(task_id)
            if not state:
                logger.warning("接口出参 /task/%s/stream: 任务不存在，结束推送", task_id)
                yield f"data: {json.dumps({'error': '任务不存在'}, ensure_ascii=False)}\n\n"
                break

            # 只推送关键状态字段
            push_data = {
                "task_id": state["task_id"],
                "status": state["status"],
                "current_step": state["current_step"],
                "total_steps": state.get("total_steps", 6),
                "step_name": state["step_name"],
                "progress": state["progress"],
                "message": state["message"],
                "warnings": state.get("warnings", []),
                "logs": state.get("logs", [])[-20:],  # 只推最近20条日志
                "output_files": state.get("output_files", {}),
            }
            yield f"data: {json.dumps(push_data, ensure_ascii=False)}\n\n"

            if state['status'] in ('completed', 'failed', 'cancelled'):
                logger.info(
                    "接口出参 /task/%s/stream: 任务结束，status=%s",
                    task_id,
                    state['status'],
                )
                break
            time.sleep(1)

    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )


@task_bp.route('/task/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    logger.info("接口入参 /task/%s/cancel: 请求取消任务", task_id)
    from app import task_manager
    success = task_manager.cancel_task(task_id)
    if success:
        resp = {"message": "任务已取消"}
        logger.info("接口出参 /task/%s/cancel: status=200, body=%s", task_id, resp)
        return jsonify(resp)
    resp = {"error": "无法取消任务（可能已完成或不存在）"}
    logger.warning("接口出参 /task/%s/cancel: status=400, body=%s", task_id, resp)
    return jsonify(resp), 400
