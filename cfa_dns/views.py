from . import cfadns

@cfadns.route('/')
def index():
    return 'Hello world.'