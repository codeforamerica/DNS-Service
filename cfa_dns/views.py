from flask import current_app, request, redirect

from . import cfadns, URL_REDIRECTS

@cfadns.route('/')
@cfadns.route('/<path:path>')
def index(path=None):
    host_parts = request.headers.get('Host', '').split('.')
    zone_parts = current_app.config['ZONE_NAME'].split('.')
    
    if host_parts[-len(zone_parts):] == zone_parts:
        host_prefix = '.'.join(host_parts[:-len(zone_parts)])
        
        redirects = [rec for rec in current_app.config['HOST_RECORDS']
                     if rec['Type'] in URL_REDIRECTS and rec['Host'] == host_prefix]
    
        if redirects:
            return redirect('{}/{}'.format(redirects[0]['Value'], path))

        return 'I might know something about {}\n'.format('.'.join(host_parts))

    return 'I know nothing of {}\n'.format('.'.join(host_parts))
