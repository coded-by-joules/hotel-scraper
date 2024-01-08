from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_cors import CORS
from .database import db
from .api_routes import api_routes
from .config import config

class Base(DeclarativeBase):
    pass

def create_app(config_mode):
    app = Flask(__name__, static_folder="../frontend_dist/assets", template_folder="../frontend_dist")
    app.config.from_object(config[config_mode])
    CORS(app)

    db.init_app(app)
    app.register_blueprint(api_routes, url_prefix="/api")

    return app
