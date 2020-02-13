import json
from typing import Any


class KPConfBase:
    DEFAULT_PREFIX = 'default_'

    def __init__(self, default_dict: dict, input_dict: dict):
        self._default_values = default_dict
        self._values = input_dict or {}

    def __getattr__(self, key: str) -> Any:
        try:
            res = self._values.get(key, None)
            return self._default_values[key] if res is None else res
        except KeyError as e:
            if key.startswith(KPConfBase.DEFAULT_PREFIX):
                try:
                    return self._default_values.get(key[len(KPConfBase.DEFAULT_PREFIX):])
                except KeyError:
                    raise AttributeError(e)
            else:
                raise AttributeError(e)

    def get_default(self, key: str) -> Any:
        return self._default_values[key]


class KPConfiguration:
    def __init__(self, path: str = 'kodiproxy.json'):
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
            self.receiver = KPConfBase({
                'desiredInput': 'AUXB',
                'ip': None,
                'port': None
            }, conf.get('receiver', None))
