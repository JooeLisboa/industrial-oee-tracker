from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import os


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'dev-secret')

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app import models  # noqa: F401
    from app.routes.api import api_bp

    app.register_blueprint(api_bp, url_prefix='/api')

    @app.get('/health')
    def health():
        return {'ok': True}

    return app
