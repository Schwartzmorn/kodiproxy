import json


class KPConfiguration:
    """Holds a bunch of configuration"""

    def __init__(self, path: str):
        with open(path) as conf:
            conf = json.loads(conf.read())

            self.jrpc = conf.get('jrpc', None)

            self.logging = conf.get('logging', None)

            self.receiver = conf.get('receiver', None)

            self.server = conf.get('server', None)
