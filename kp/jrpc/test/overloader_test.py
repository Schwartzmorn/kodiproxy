import json
from kp.jrpc.jrpcserver import JRPCOverloader
import unittest
from unittest.mock import MagicMock


class MockOverloader(JRPCOverloader):
    def overload_query(self, params):
        pass


class TestOverloader(unittest.TestCase):
    def test_handle(self):
        overloader = MockOverloader()
        overloader.overload_query = MagicMock(return_value=(
            205, {'res_prop': 'res value'}, {'header_key': 'header value'}))

        code, res, headers = overloader.handle_query({
            'id': 666,
            'params': {
                'param_key': 'param value'
            }
        })

        self.assertEqual(code, 205)
        res_json = json.loads(res)
        self.assertEqual(res_json, {
            'id': 666,
            'jsonrpc': '2.0',
            'result': {
                'res_prop': 'res value'
            }
        })
        self.assertEqual(int(headers['content-length']), len(res))
        self.assertEqual(headers['content-type'],
                         'application/json; charset=utf-8')
        self.assertEqual(headers['header_key'], 'header value')

        overloader.overload_query.assert_called_once_with(
            {'param_key': 'param value'})
