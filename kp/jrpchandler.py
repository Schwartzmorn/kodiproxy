import logging
from socket import timeout
from urllib import error, request
import time

LOGGER = logging.getLogger('kodiproxy')

class JRPCHandler:
    def __init__(self, target):
        self.target = target

    def return_error(self, code, payload):
        return code, payload, { 'Content-type': 'text/plain' }

    def forward(self, headers, jrpc_request):
        LOGGER.debug('Forwarding query to Kodi %s', jrpc_request)
        time.sleep(0.1)
        req = request.Request(self.target,
                data = jrpc_request,
                headers = headers)
        try:
            with request.urlopen(req, timeout = 5) as res:
                LOGGER.debug('Received response with code %s', res.getcode())
                length = int(res.headers['Content-Length'])
                payload = res.read(length)
                LOGGER.debug('Payload received: %s', payload)
                return res.getcode(), payload, res.info()
        except timeout:
            LOGGER.error('Request to Kodi timeouted')
            return self.return_error(408, b'Request to Kodi timeouted')
        except error.HTTPError as e:
            LOGGER.warning('Request to Kodi failed with error: %s', e)
            return self.return_error(e.code, b'Request to Kodi failed')
        except Exception as e:
            LOGGER.error('Something went wrong while calling Kodi: %s', e)
            return self.return_error(500, b'Unknown error')

    def dispatch(self, headers, jrpc_request):
        return self.forward(headers, jrpc_request)
