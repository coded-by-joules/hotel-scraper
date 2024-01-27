from flask import render_template, url_for
from backend import app, db
from backend.database import *
from backend.api_routes import api_routes
from backend.socket_config import socket_io

app.register_blueprint(api_routes, url_prefix="/api")
debug_mode = True


@app.route("/")
def hello():
    if app.debug:
        return "Hello world"
    else:
        return render_template("index.html")


if (__name__ == "__main__"):
    with app.app_context():
        db.create_all()

    if debug_mode:
        app.run(host='localhost', port=5000, debug=debug_mode)
    else:
        socket_io.run(app, host="127.0.0.1", port=5000, debug=debug_mode)
