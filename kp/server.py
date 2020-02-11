import http.server
from kp.jrpchandler import JRPCHandler
import logging
from socket import timeout
from urllib import parse

LOGGER = logging.getLogger('kodiproxy')

class KodiProxyServer:
    def __init__(self, conf):
        jrpc_handler = JRPCHandler(conf.target)
        KodiProxyHandler._JRPC_HANDLER = jrpc_handler
        LOGGER.info('Creating server %s:%d', conf.host, conf.port)
        self.httpd = http.server.HTTPServer((conf.host, conf.port), KodiProxyHandler)

    def serve(self):
        LOGGER.info('Starting server...')
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        LOGGER.info('Stopping server')
        self.httpd.server_close()

class KodiProxyHandler(http.server.BaseHTTPRequestHandler):
    _JRPC_PATH = '/jsonrpc'
    _JRPC_HANDLER = None

    def answer_error(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(message)

    def log_message(self, format, *args):
        return

    def dispatch_jrpc(self, request):
        headers = dict((k, v) for k, v in self.headers.items())
        code, payload, headers = KodiProxyHandler._JRPC_HANDLER.dispatch(headers, request)
        try:
            self.send_response(code)
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)
            LOGGER.debug('Response from Kodi successfully sent')
        except Exception as e:
            LOGGER.error('Failed to send response with error: %s', e)

    def do_GET(self):
        (_, _, path, _, query, _) = parse.urlparse(self.path)
        LOGGER.info('Received GET %s', path)
        if path != KodiProxyHandler._JRPC_PATH:
            self.answer_error(404, 'Not found')
        else:
            params = parse.parse_qs(query)
            if 'request' not in params or len(params) != 1 or len(params['request']) != 1:
                self.answer_error(400, 'Bad request')
            else:
                self.dispatch_jrpc(bytes(params['request'][0], 'utf-8'))

    def do_POST(self):
        (_, _, path, _, _, _) = parse.urlparse(self.path)
        LOGGER.info('Received POST %s', path)
        LOGGER.debug('%s', self.headers)
        if path != KodiProxyHandler._JRPC_PATH:
            self.answer_error(404, 'Not found')
        else:
            length = int(self.headers['Content-Length'])
            self.dispatch_jrpc(self.rfile.read(length))

    def do_HEAD(self):
        # TODO nice to have
        LOGGER.warning('HEAD')

