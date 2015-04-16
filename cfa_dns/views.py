from flask import current_app, request, jsonify

from . import cfadns

@cfadns.route('/')
def index():
    response = dict(
        hostname = request.headers.get('Host', '-'),
        records = current_app.config['HOST_RECORDS']
        )
    
    return jsonify(response)