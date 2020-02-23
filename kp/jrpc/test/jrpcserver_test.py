import kp.jrpc.jrpcserver
from kp.log import config_logger
import unittest
from unittest.mock import MagicMock, patch

config_logger({
    'type': 'null'
})


class TestJRPCHandler(unittest.TestCase):
    @patch('kp.jrpc.jrpcserver.request.Request')
    @patch('kp.jrpc.jrpcserver.request.urlopen')
    def test_error_decoding(self, open_mock, request_mock):
        '''If we fail to decode the request, we forward it'''

        # Prepare mocks
        res_mock = MagicMock()
        open_mock.return_value = MagicMock()
        open_mock.return_value.__enter__ = MagicMock(return_value=res_mock)
        res_mock.getcode.return_value = 666
        res_mock.read.return_value = b'result'
        res_mock.info.return_value = {'content-length': '39'}

        # Actual test
        handler = kp.jrpc.jrpcserver.JRPCHandler(
            'http://mock_url', MagicMock(), b'"astring"', {'Header': 'header-value'})

        code, payload, headers = handler.dispatch()

        # Checks
        self.assertEqual(code, 666)
        self.assertEqual(payload, b'result')
        self.assertEqual(headers, {'content-length': '39'})
        res_mock.read.assert_called_once_with(39)

        open_mock.assert_called_once()
        args, kwargs = request_mock.call_args
        self.assertEqual(args[0], 'http://mock_url')
        self.assertEqual(kwargs['data'], b'"astring"')
        self.assertEqual(kwargs['headers'], {'Header': 'header-value'})

        handler.overloaders.get.assert_not_called()

    @patch('kp.jrpc.jrpcserver.request.Request')
    @patch('kp.jrpc.jrpcserver.request.urlopen')
    def test_no_match(self, open_mock, request_mock):
        '''Check that if no overloader matches, we forward the query'''
        # Prepare mocks
        res_mock = MagicMock()
        open_mock.return_value = MagicMock()
        open_mock.return_value.__enter__ = MagicMock(return_value=res_mock)
        res_mock.getcode.return_value = 666
        res_mock.read.return_value = b'result'
        res_mock.info.return_value = {'content-length': '39'}

        payload = b'{"id": 254, "method": "any_other_method", "params": "parameters"}'

        overloaders_mock = MagicMock()
        overloaders_mock.get.return_value = None

        handler = kp.jrpc.jrpcserver.JRPCHandler(
            'http://mock_url', overloaders_mock, payload, {'Header': 'header-value'})

        code, response, headers = handler.dispatch()

        # Checks
        self.assertEqual(code, 666)
        self.assertEqual(response, b'result')
        self.assertEqual(headers, {'content-length': '39'})
        res_mock.read.assert_called_once_with(39)

        handler.overloaders.get.assert_called_once_with(
            'any_other_method', None)

    def test_match(self):
        '''Check that if an overloader matches, it handles the query'''
        overloader_mock = MagicMock()
        overloader_provider_mock = MagicMock(return_value=overloader_mock)

        overloader_mock.handle_query.return_value = 666, b'response', {
            'Header': 'header-value'}

        overloaders = {'some_method': overloader_provider_mock}

        payload = b'{"id": 254, "method": "some_method", "params": "parameters"}'

        handler = kp.jrpc.jrpcserver.JRPCHandler(
            'http://mock_url', overloaders, payload, {})
        code, response, headers = handler.dispatch()

        self.assertEqual(code, 666)
        self.assertEqual(response, b'response')
        self.assertEqual(headers, {'Header': 'header-value'})

        overloader_mock.handle_query.assert_called_once_with(
            {"id": 254, "method": "some_method", "params": "parameters"})
