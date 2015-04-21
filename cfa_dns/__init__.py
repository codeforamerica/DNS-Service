from sys import stderr
from csv import DictReader
from urlparse import urlparse
from os.path import dirname, join, basename
from hashlib import sha1
from os import environ
import json

from flask import Blueprint, Flask
from .api import check_upstream

URL_REDIRECTS = 'URL', 'URL301'

allowed_types = ('A', 'CNAME', 'MX', 'AAAA', 'TXT', 'FRAME', 'NS') + URL_REDIRECTS
allowed_ttls = range(60, 172801)

cfadns = Blueprint('gloss', __name__)

def create_app(environ):
    
    filename = join(dirname(__file__), '..', 'host-records.csv')
    check_file(filename)

    check_upstream(environ['DNS_API_BASE'], environ['DNS_API_KEY'])
    
    with open(filename) as file:
        host_records = list(DictReader(file))

    app = Flask(__name__)
    app.config['HOST_RECORDS'] = host_records
    app.config['ZONE_NAME'] = environ['ZONE_NAME']
    app.register_blueprint(cfadns)
    return app

def normalize(row):
    return tuple(sorted(row.items()))

def check_file(filename):
    '''
    '''
    with open(filename) as file:
        found_rows = list(DictReader(file))
    
    hosts = []
    
    # Are types and TTLs all as expected?
    for (index, row) in enumerate(found_rows):
        row.update(dict(source='{} row {}'.format(filename, index+1)))
    
        assert row['Type'] in allowed_types, '"{Type}" is a bad record type, {source}'.format(**row)
        assert int(row['TTL']) in allowed_ttls, '"{TTL}" is a bad TTL, {source}'.format(**row)
        
        if row['Type'] in URL_REDIRECTS:
            scheme = urlparse(row['Value']).scheme
            assert scheme in ('http', 'https'), '"{Value}" is a bad redirect, {source}'.format(**row)
        
        host = dict(
            type=row['Type'],
            name=row['Host'],
            value=row['Value'],
            ttl=row['TTL'],
            mxpref=row['MXPref']
            )
        
        hosts.append(host)

    serialized = json.dumps(sorted(hosts), ensure_ascii=True, separators=(',', ':'))
    hash = sha1(serialized).hexdigest()
    
    print >> stderr, '{} checks out with hash "{}"'.format(basename(filename), hash)

from . import views
