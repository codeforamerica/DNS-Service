from time import time
from flask import current_app, jsonify

from . import cfadns
from .api import check_upstream

@cfadns.route('/')
def index():
    return 'Go away.'

@cfadns.route('/.well-known/status')
def well_known_status():
    '''
    '''
    response = dict(status=None, updated=int(time()),
                    dependencies=['NameCheap'], resources={})

    try:
        check_upstream(current_app.config['DNS_API_BASE'], current_app.config['DNS_API_KEY'])
    except Exception as e:
        response['status'] = str(e)
    else:
        response['status'] = 'ok'
        
    return jsonify(response)
