import json

class KPConfBase:
    DEFAULT_PREFIX = 'default_'

    def __init__(self, default_dict, input_dict):
        self._default_values = default_dict
        self._values = input_dict or {}

    def __getattr__(self, key):
        try:
            res = self._values.get(key, None)
            return self._default_values[key] if res is None else res
        except KeyError as e:
            if key.startswith(KPConfBase.DEFAULT_PREFIX):
                try:
                    return self._default_values(key[len(KPConfBase.DEFAULt_PREFIX)])
                except KeyError:
                    raise AttributeError(e)
            else:
                raise AttributeError(e)

    def get_default(self, key):
        return self._default_values[key]

class KPConfiguration:
    def __init__(self, path = 'kodiproxy.json'):
        with open(path) as conf:
            conf = json.loads(conf.read())
            self.logging = KPConfBase({
                    'enabled': True,
                    'level': 'DEBUG',
                    'path': 'kodiproxy_log.txt'
                },
                conf.get('logging', None))
            self.server = KPConfBase({
                    'host': '',
                    'port': 8080,
                    'target': 'http://localhost:8081/jsonrpc'
                },
                conf.get('server', None))
