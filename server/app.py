"""Flask主应用"""
from flask import Flask
from flask_cors import CORS

from config import Config
from task.task_manager import TaskManager
from utils.file_manager import FileCleanupWorker, FileManager

# 全局任务管理器实例
task_manager = TaskManager(
    max_workers=Config.MAX_CONCURRENT_TASKS,
    data_dir=str(Config.TASK_DATA_DIR)
)


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册蓝图
    from api.generate import generate_bp
    from api.task import task_bp
    from api.download import download_bp

    app.register_blueprint(generate_bp, url_prefix='/api')
    app.register_blueprint(task_bp, url_prefix='/api')
    app.register_blueprint(download_bp, url_prefix='/api')

    # 确保输出目录存在
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    Config.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    Config.TASK_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 启动后台文件清理线程（默认开启）
    if Config.ENABLE_FILE_CLEANUP:
        file_manager = FileManager(
            output_dir=Config.OUTPUT_DIR,
            screenshot_dir=Config.SCREENSHOT_DIR,
            task_data_dir=Config.TASK_DATA_DIR,
            retention_hours=Config.FILE_RETENTION_HOURS,
        )
        cleanup_worker = FileCleanupWorker(
            file_manager=file_manager,
            interval_minutes=Config.FILE_CLEANUP_INTERVAL_MINUTES,
        )
        cleanup_worker.start()
        app.extensions["file_cleanup_worker"] = cleanup_worker

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
