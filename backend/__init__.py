from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_cors import CORS

app = Flask(__name__, static_folder="../frontend_dist/assets", template_folder="../frontend_dist")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///hotels.db"
CORS(app)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(app, model_class=Base)
