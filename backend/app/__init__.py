from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from backend.config import Config
from backend.app.errors import register_error_handlers


db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migration_directory = Path(__file__).resolve().parents[1] / "migrations"
    migrate.init_app(app, db, directory=str(migration_directory))
    if "*" in app.config["CORS_ORIGINS"]:
        raise RuntimeError("CORS_ORIGINS must explicitly list trusted frontend origins")
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=False)
    register_error_handlers(app)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; connect-src 'self' http://localhost:5173 http://127.0.0.1:5173; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    from backend.app.models import register_models
    register_models()
    from backend.app.routes.auth import auth_bp
    from backend.app.routes.algorithms import algorithms_bp
    from backend.app.routes.resources import resources_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(algorithms_bp)
    app.register_blueprint(resources_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "blood-supply-api"})

    return app
