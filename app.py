from flask import render_template
from backend import create_app
from backend.database import db
import os
from dotenv import load_dotenv

load_dotenv()

config_mode = os.getenv("CONFIG_MODE")
app = create_app(config_mode)
celery_app = app.extensions["celery"]

@app.route("/")
def hello():
    if config_mode in ["development", "testing"]:
        return "Hello world"
    else:
        return render_template("index.html")

if (__name__ == "__main__"):
    with app.app_context():
        db.create_all()
    app.run()
