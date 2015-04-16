from flask import Blueprint, Flask

cfadns = Blueprint('gloss', __name__)

def create_app(environ):
    app = Flask(__name__)
    app.register_blueprint(cfadns)
    return app

from . import views
