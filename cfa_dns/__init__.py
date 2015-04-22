from sys import stderr
from csv import DictReader
from urlparse import urlparse
from os.path import dirname, join, basename
from os import environ

from flask import Blueprint, Flask
from .api import format_csv_row, hash_host_records, check_upstream, push_upstream

URL_REDIRECTS = 'URL', 'URL301'

allowed_types = ('A', 'CNAME', 'MX', 'AAAA', 'TXT', 'FRAME', 'NS') + URL_REDIRECTS
allowed_ttls = range(60, 172801)

cfadns = Blueprint('gloss', __name__)

def create_app(environ):
    
    filename = join(dirname(__file__), '..', 'host-records.csv')
    check_file(filename)

    dns_api_base, dns_api_key = environ['DNS_API_BASE'], environ['DNS_API_KEY']
    check_upstream(dns_api_base, dns_api_key)
    
    with open(filename) as file:
        host_records = list(DictReader(file))
    
    push_upstream(dns_api_base, dns_api_key, host_records)

    app = Flask(__name__)
    app.config['DNS_API_BASE'] = dns_api_base
    app.config['DNS_API_KEY'] = dns_api_key
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
    
        if row['Type'] not in allowed_types:
            raise ValueError('"{Type}" is a bad record type, {source}'.format(**row))
        
        if int(row['TTL']) not in allowed_ttls:
            raise ValueError('"{TTL}" is a bad TTL, {source}'.format(**row))
        
        if row['Type'] in URL_REDIRECTS:
            scheme = urlparse(row['Value']).scheme
            
            if scheme not in ('http', 'https'):
                raise ValueError('"{Value}" is a bad redirect, {source}'.format(**row))
        
        hosts.append(format_csv_row(row))

    hash = hash_host_records(hosts)
    
    print >> stderr, '{} checks out with hash "{}"'.format(basename(filename), hash)

from . import views
