from csv import DictReader
from os.path import dirname, join
from flask import Blueprint, Flask
from .test import test_file

cfadns = Blueprint('gloss', __name__)

def create_app(environ):

    filename = join(dirname(__file__), '..', 'host-records.csv')
    test_file(filename)
    
    with open(filename) as file:
        host_records = list(DictReader(file))

    app = Flask(__name__)
    app.config['HOST_RECORDS'] = host_records
    app.config['ZONE_NAME'] = environ['ZONE_NAME']
    app.register_blueprint(cfadns)
    return app

from . import views
