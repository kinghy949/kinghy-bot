"""Flask 应用入口"""
from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return {"status": "ok", "app": "{{SOFTWARE_NAME}}"}

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
