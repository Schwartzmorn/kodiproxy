import json
from kp.regression.mock_server import MockServer
import unittest
from urllib import error, request
from typing import Any, Tuple


class RegressionCase(unittest.TestCase):
    JRPC_MOCK = None
    RECEIVER_MOCK = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.jrpc_mock: MockServer = RegressionCase.JRPC_MOCK
        self.receiver_mock: MockServer = RegressionCase.RECEIVER_MOCK

    def setUp(self) -> None:
        self.jrpc_mock.reset_mocks()
        self.receiver_mock.reset_mocks()

    def assertPayloadEqual(self, response, expected: Any):
        expected = {
            'jsonrpc': '2.0',
            'id': 321,
            'result': expected
        }
        self.assertEqual(response, response)

    def open_jrpc(self, method: str, params: dict) -> Tuple[int, dict]:
        """Helper function to send jrpc query to the proxy"""
        payload = {
            'jsonrpc': '2.0',
            'id': 321,
            'method': method,
            'params': params
        }

        headers = {'Content-Type': 'application/json'}
        req = request.Request('http://localhost:43210/jsonrpc',
                              data=bytes(json.dumps(payload), 'utf-8'), headers=headers)
        try:
            res = request.urlopen(req)
            code = res.getcode()
            payload = json.load(res)
        except error.HTTPError as e:
            code = e.getcode()
            payload = None

        return code, payload
