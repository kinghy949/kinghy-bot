"""Flask主应用"""
from flask import Flask
from flask_cors import CORS

from config import Config
from task.task_manager import TaskManager

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

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
