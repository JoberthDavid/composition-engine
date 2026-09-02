from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    from app.routes.health import health_bp

    app.register_blueprint(health_bp)

    return app
