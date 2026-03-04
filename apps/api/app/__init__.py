import logging
import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", "dev-secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=int(os.getenv("JWT_EXPIRES_HOURS", "12")))
    app.config["ENV"] = os.getenv("FLASK_ENV", "production")

    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

    if test_config:
        app.config.update(test_config)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=False)

    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return jsonify({"error": {"code": 401, "message": reason}}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"error": {"code": 401, "message": reason}}), 401

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        return jsonify({"error": {"code": 401, "message": "Token has expired"}}), 401

    from app import models  # noqa: F401
    from app.routes.api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        app.logger.warning("HTTP error %s: %s", err.code, err.description)
        return jsonify({"error": {"code": err.code, "message": err.description}}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        app.logger.exception("Unhandled exception: %s", err)
        message = "Internal server error"
        if app.config.get("ENV") == "development":
            message = str(err)
        return jsonify({"error": {"code": 500, "message": message}}), 500

    return app
