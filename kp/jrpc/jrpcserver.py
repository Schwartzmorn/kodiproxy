from abc import abstractmethod, ABCMeta
import json
from unittest.mock import Base
from kp.confbase import KPConfBase
from kp.types import Headers, Response
import logging
from socket import timeout
from urllib import error, request
import traceback
from typing import Any, Callable, Dict, Tuple

LOGGER = logging.getLogger('kodiproxy')


class JRPCOverloader(metaclass=ABCMeta):
    """Base class of the JRPC overloaders"""

    def handle_query(self, query: dict) -> Response:
        self.id = query.get('id', None)
        code, payload, headers = self.overload_query(
            query.get('params', None))
        response, headers = self._enrich_http({'result': payload}, headers)
        return code, response, headers

    def _enrich_http(self, payload: dict, headers: Headers = None) -> Tuple[bytes, Headers]:
        headers = headers or dict()
        response = {
            'jsonrpc': '2.0',
            'id': self.id
        }
        response.update(payload)
        response = bytes(json.dumps(response), 'utf-8')
        headers['content-length'] = str(len(response))
        headers['content-type'] = 'application/json; charset=utf-8'
        return response, headers

    @abstractmethod
    def overload_query(self, params: Any) -> Tuple[int, Any, Headers]:
        pass


class JRPCHandler:
    """Dispatches the jrpc requests either to the actual JRPC server or an overloader"""

    def __init__(self, target: str,
                 overloaders: Dict[str, Callable[[], JRPCOverloader]],
                 jrpc_request: bytes, headers: Headers):
        self.headers = headers
        self.jrpc_request = jrpc_request
        self.overloaders = overloaders
        self.target = target

    def _read(self, response: Any) -> bytes:
        length = response.info()['content-length']
        return response.read(int(length)) if length else response.read()

    def _get_overloader(self, req: dict) -> JRPCOverloader:
        provider = self.overloaders.get(
            req.get('method', '__none__'), None)
        return provider(self) if provider else None

    def _return_error(self, code: int, payload) -> Response:
        return code, payload, {'content-type': 'text/plain'}

    def _forward_error(self, err: error.HTTPError) -> Response:
        return err.getcode(), self._read(err), err.info()

    def dispatch(self) -> Response:
        """Handles a jrpc request."""
        req = None
        overloader = None
        try:
            req = json.loads(self.jrpc_request)
            overloader = self._get_overloader(req)
        except Exception as e:
            LOGGER.warning(
                'Could not decode jrpc request with error "%s". Will try forwarding it', e)
            LOGGER.debug(traceback.format_exc())
        if overloader:
            try:
                return overloader.handle_query(req)
            except error.HTTPError as e:
                return self._forward_error(e)
            except Exception as e:
                LOGGER.error('Something went wrong with the overloader: %s', e)
                LOGGER.info('Trace: %s', traceback.format_exc())
                return 500, bytes('Unkown error occurred', 'ascii'), {}
        return self.forward(self.jrpc_request, self.headers)

    def forward(self, jrpc_request: bytes, headers: Headers) -> Response:
        """Send a jrpc request to the actual jrpc server"""
        LOGGER.debug('Forwarding query to jrpc server %s: %s',
                     self.target, jrpc_request)
        req = request.Request(self.target,
                              data=jrpc_request,
                              headers=headers)
        try:
            with request.urlopen(req, timeout=5) as res:
                LOGGER.debug('Received response with code %s', res.getcode())
                payload = self._read(res)
                LOGGER.debug('Payload received: %s', payload)
                return res.getcode(), payload, res.info()
        except timeout:
            LOGGER.error('Request to jrpc server timeouted')
            return self._return_error(408, b'Request to the jrpc server timeouted')
        except error.HTTPError as e:
            LOGGER.warning(
                'Request to the jrpc server failed with error: %s', e)
            return self._forward_error(e)
        except Exception as e:
            LOGGER.error(
                'Something went wrong while calling the jrpc server: %s', e)
            LOGGER.info('Trace: %s', traceback.format_exc())
            return self._return_error(500, b'Unknown error')


class JRPCOverloaderWithHandler(JRPCOverloader):
    """Base class for overloaders able to forward queries the jrpc server"""

    def __init__(self, handler: JRPCHandler):
        super().__init__()
        self.jrpc_handler = handler

    def forward(self, method: str, params: dict) -> Response:
        """Forwards a query to the jrpc server"""
        payload = {
            'method': method,
            'params': params
        }
        headers = self.jrpc_handler.headers
        payload, headers = self._enrich_http(payload, headers)

        return self.jrpc_handler.forward(payload, headers)


class JRPCServer:
    """Provides jrpc handler for request, with set targets and overloaders"""

    _DEFAULT_CONFIGURATION = {
        'target': 'http://localhost:8081/jsonrpc'
    }

    def __init__(self, conf):
        conf = KPConfBase(JRPCServer, conf)
        LOGGER.info('JRPC configuration:\n%s', conf)
        self.overloaders: Dict[str, Callable[[
            JRPCHandler], JRPCOverloader]] = {}
        self.target = conf.target

    def get_handler(self, jrpc_request: bytes, headers: Headers) -> JRPCHandler:
        return JRPCHandler(self.target, self.overloaders, jrpc_request, headers)

    def register_overloader(self, method: str, overloader_provider: Callable[[JRPCHandler], JRPCOverloader]) -> None:
        """Register an overloader provider on a jrpc method"""
        self.overloaders[method] = overloader_provider
