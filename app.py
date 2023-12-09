from backend import app, db
from backend.database import *
from backend.api_routes import api_routes


app.register_blueprint(api_routes, url_prefix="/api")


@app.route("/")
def hello():
    return "Hello world"


if (__name__ == "__main__"):
    with app.app_context():
        db.create_all()
    app.run(host='localhost', port=5000, debug=True)
