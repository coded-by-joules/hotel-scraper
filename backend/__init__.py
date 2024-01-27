from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_cors import CORS
from .socket_config import socket_io

app = Flask(__name__, static_folder="../frontend/dist/assets",
            template_folder="../frontend/dist/")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///hotels.db"
CORS(app)
socket_io.init_app(app, cors_allowed_origins="*")


db = SQLAlchemy(app)
