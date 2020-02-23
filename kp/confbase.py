from typing import Any


class KPConfBase:
    """Holds a bunch of key/values with default values"""
    DEFAULT_PREFIX = 'default_'

    def __init__(self, class_conf: type, input_dict: dict):
        self._default_values: dict = class_conf._DEFAULT_CONFIGURATION
        self._values = input_dict or {}

    def __getattr__(self, key: str) -> Any:
        try:
            res = self._values.get(key, None)
            return self._default_values[key] if res is None else res
        except KeyError:
            if key.startswith(KPConfBase.DEFAULT_PREFIX):
                try:
                    return self._default_values.get(key[len(KPConfBase.DEFAULT_PREFIX):])
                except KeyError:
                    pass
            raise AttributeError(
                'Configuration has no member "{}"'.format(key))

    def get_default(self, key: str) -> Any:
        return self._default_values[key]

    def __str__(self) -> str:
        return '\n'.join(map(lambda k: '{}: {}'.format(k, getattr(self, k)), self._default_values.keys()))
