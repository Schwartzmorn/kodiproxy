import json
from kp.types import Headers, Response
import logging
from socket import timeout
from urllib import error, request
from typing import Callable, Dict

LOGGER = logging.getLogger('kodiproxy')


class JRPCOverloader:
    def handle_query(self, payload: dict) -> Response:
        self.id = payload.get(id, None)
        code, payload, headers = self.overload_query(payload)
        return self._enrich_response(code, payload, headers)

    def _enrich_response(self, code: int, payload, headers: Headers) -> Response:
        payload = {
            'jsonrpc': '2.0',
            'id': self.id,
            'result': payload
        }
        payload = bytes(json.dumps(payload), 'utf-8')
        headers['content-length'] = str(len(payload))
        headers['content-type'] = 'application/json'
        return code, payload, headers

    def overload_query(self, payload: dict) -> Response:
        raise NotImplementedError(
            'A JRPCOverloader must implement method "overload_query"')

    @classmethod
    def GET_METHOD(cls):
        cls.METHOD  # pylint: disable=no-member


class JRPCHandler:
    def __init__(self, target, overloaders):
        self.target = target
        self.overloaders = overloaders

    def _return_error(self, code: int, payload) -> Response:
        return code, payload, {'Content-type': 'text/plain'}

    def _forward(self, headers: dict, jrpc_request: bytes) -> Response:
        LOGGER.debug('Forwarding query to Kodi %s', jrpc_request)
        req = request.Request(self.target,
                              data=jrpc_request,
                              headers=headers)
        try:
            with request.urlopen(req, timeout=5) as res:
                LOGGER.debug('Received response with code %s', res.getcode())
                length = int(res.headers['Content-Length'])
                payload = res.read(length)
                LOGGER.debug('Payload received: %s', payload)
                return res.getcode(), payload, res.info()
        except timeout:
            LOGGER.error('Request to Kodi timeouted')
            return self._return_error(408, b'Request to Kodi timeouted')
        except error.HTTPError as e:
            LOGGER.warning('Request to Kodi failed with error: %s', e)
            return self._return_error(e.code, b'Request to Kodi failed')
        except Exception as e:
            LOGGER.error('Something went wrong while calling Kodi: %s', e)
            return self._return_error(500, b'Unknown error')

    def dispatch(self, headers: dict, jrpc_request: bytes) -> Response:
        return self._forward(headers, jrpc_request)


class JRPCServer:
    def __init__(self, target):
        self.overloaders: Dict[str, Callable[[], JRPCOverloader]] = {}
        self.target = target

    def register_overloader(self, method: str, overloader_provider: Callable[[], JRPCOverloader]):
        self.overloaders[method] = overloader_provider

    def get_handler(self, target: str) -> JRPCHandler:
        return JRPCHandler(self.target, self.overloaders)


class SetVolumeOverloader(JRPCOverloader):
    METHOD = 'Application.SetVolume'

    def __init__(self, jrpc_handler: JRPCHandler):
        JRPCOverloader.__init__(self, jrpc_handler)

    def overload_query(self, payload):
        pass
