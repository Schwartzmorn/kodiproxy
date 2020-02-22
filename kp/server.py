import http.server
from kp.confbase import KPConfBase
from kp.jrpc.jrpcserver import JRPCServer
import logging
import socketserver
from socket import timeout
import traceback
from urllib import parse

LOGGER = logging.getLogger('kodiproxy')


class KodiProxyServer:
    """Class to create the Kodi proxy"""

    _DEFAULT_CONFIGURATION = {
        'host': '',
        'port': 8080
    }

    @staticmethod
    def ProvideProxyHandler(jrpc_path: str, jrpc_server: JRPCServer):
        class KodiProxyHandler(http.server.BaseHTTPRequestHandler):
            """Class to handle all the http requests"""

            def __init__(self, *args, **kwargs):
                self.jrpc_path = jrpc_path
                self.jrpc_server = jrpc_server
                super(KodiProxyHandler, self).__init__(*args, **kwargs)

            def log_message(self, format, *args) -> None:
                return

            def _dispatch_jrpc(self, request) -> None:
                headers = dict()
                for k, v in self.headers.items():
                    headers[k.lower()] = v
                handler = self.jrpc_server.get_handler(
                    request, headers)
                code, payload, headers = handler.dispatch()
                try:
                    self.send_response(code)
                    for k, v in headers.items():
                        self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(payload)
                    LOGGER.debug(
                        'Reponse payload successfully sent: %s', payload)
                except Exception as e:
                    LOGGER.error('Failed to send response with error: %s', e)
                    LOGGER.info('Trace: %s', traceback.format_exc())

            def do_GET(self) -> None:
                (_, _, path, _, query, _) = parse.urlparse(self.path)
                LOGGER.info('Received GET %s', path)
                if path != self.jrpc_path:
                    self.send_error(404)
                else:
                    params = parse.parse_qs(query)
                    if ('request' not in params) or (len(params) != 1) or (len(params['request']) != 1):
                        self.send_error(400)
                    else:
                        self._dispatch_jrpc(
                            bytes(params['request'][0], 'utf-8'))

            def do_POST(self) -> None:
                (_, _, path, _, _, _) = parse.urlparse(self.path)
                LOGGER.info('Received POST %s', path)
                LOGGER.debug('%s', self.headers)
                if path != self.jrpc_path:
                    self.send_error(404)
                else:
                    # works whether content-length is present or not
                    length = self.headers['content-length']
                    payload = self.rfile.read(
                        int(length)) if length else self.rfile.read()
                    self._dispatch_jrpc(payload)

            def do_HEAD(self) -> None:
                # TODO nice to have
                LOGGER.warning('HEAD')

        return KodiProxyHandler

    def __init__(self, conf,  jrpc_server: JRPCServer):
        conf = KPConfBase(KodiProxyServer, conf)
        LOGGER.info('Creating server %s:%d', conf.host, conf.port)
        LOGGER.info('Server configuration:\n%s', conf)
        self.port = conf.port
        self.httpd = http.server.ThreadingHTTPServer(
            (conf.host, conf.port), KodiProxyServer.ProvideProxyHandler('/jsonrpc', jrpc_server))

    def serve(self) -> None:
        """Starts the server"""
        LOGGER.info('Starting server...')
        try:
            self.httpd.serve_forever(poll_interval=0.05)
        except KeyboardInterrupt:
            pass
        LOGGER.info('Stopping server')
        self.httpd.server_close()

    def shutdown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
