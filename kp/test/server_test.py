from kp import log, server
import threading
from typing import Tuple
import unittest
from unittest.mock import ANY, MagicMock
from urllib import error, request


def serve(httpd: server.KodiProxyServer):
    httpd.serve()


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.jrpc_mock = MagicMock()
        cls.server = server.KodiProxyServer({
            'ip': '0.0.0.0',
            'port': 43210
        }, cls.jrpc_mock)
        cls.thread = threading.Thread(
            target=serve, args=[cls.server])
        cls.thread.start()
        log.config_logger({
            'type': 'null'
        })

    def setUp(self):
        self.jrpc_mock.reset_mock(return_value=True, side_effect=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.httpd.shutdown()
        cls.thread.join()

    def open(self, url: str, data: bytes = None, headers: dict = {}) -> Tuple[int, bytes, dict]:
        try:
            req = request.Request(
                'http://0.0.0.0:43210/{}'.format(url),
                data=data,
                headers=headers
            )
            res = request.urlopen(req)
            return res.getcode(), res.read(), res.info()
        except error.HTTPError as e:
            return e.getcode(), e.read(), e.headers

    def test_error_get(self) -> None:
        code, _, _ = self.open('test')
        self.assertEqual(code, 404)

        code, _, _ = self.open('jsonrpc')
        self.assertEqual(code, 400)

        code, _, _ = self.open('jsonrpc?invalid=invalid')
        self.assertEqual(code, 400)

    def test_error_post(self) -> None:
        code, _, _ = self.open('test', b'some payload')
        self.assertEqual(code, 404)

    def test_dispatch_get(self) -> None:
        handler = MagicMock()
        self.jrpc_mock.get_handler.return_value = handler
        handler.dispatch.return_value = (200, b'handler_response', {
                                         'handler_header': 'handler_header_value'})
        code, payload, headers = self.open('jsonrpc?request=jrpc%3Dpayload')

        self.assertEqual(code, 200)
        self.assertEqual(payload, b'handler_response')
        self.assertIn('handler_header', headers)
        self.assertEqual(headers['handler_header'], 'handler_header_value')

        self.jrpc_mock.get_handler.assert_called_once_with(
            b'jrpc=payload', ANY)
        handler.dispatch.assert_called_once()

    def test_dispatch_post(self) -> None:
        handler = MagicMock()
        self.jrpc_mock.get_handler.return_value = handler
        handler.dispatch.return_value = (200, b'handler_response', {})
        self.open('jsonrpc', data=b'jrpc%3Dpayload')

        self.jrpc_mock.get_handler.assert_called_once_with(
            b'jrpc%3Dpayload', ANY)
        handler.dispatch.assert_called_once()
