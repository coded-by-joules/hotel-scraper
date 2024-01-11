from flask import Flask
from .celery_setup import celery_init_app
from flask_cors import CORS
from .database import db
from .api_routes import api_routes
from .config import config
from flask_migrate import Migrate
import os

def create_app(config_mode):
    app = Flask(__name__, static_folder="../frontend_dist/assets", template_folder="../frontend_dist")
    app.config.from_object(config[config_mode])
    app.config.from_mapping(
        CELERY=dict(
            broker_url=app.config['REDIS_URL'],
            result_backend=app.config['REDIS_URL'],
            task_ignore_result=True
        ),
    )
    app.config.from_prefixed_env()
    CORS(app)
    migrate = Migrate()

    db.init_app(app)
    migrate.init_app(app, db)   
    app.register_blueprint(api_routes, url_prefix="/api")

    celery_init_app(app)
    return app
