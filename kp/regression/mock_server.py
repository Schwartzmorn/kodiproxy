import http.server
from urllib import parse
import threading
from typing import Any, Dict, List, Tuple


class MockResponse:
    """Small class to help mock response of an HTTP server"""

    def __init__(self, responses: Tuple[int, bytes],
                 method: str = None, path: str = None) -> None:
        self.index = 0
        self.responses = responses
        self.method = method
        self.path = path

    def match(self, method: str, path: str) -> bool:
        """Returns whether this mock fits the request"""
        if self.method is not None and self.method != method:
            return False
        if self.path is not None and self.path != path:
            return False
        return True

    def get_response(self) -> Tuple[int, bytes]:
        """Returns the current response to send. It cycles through its responses"""
        res = self.responses[self.index]
        self.index = (self.index + 1) % len(self.responses)
        return res


class MockQuery:
    """Small class to help keep track of the queries made to the HTTP server"""

    def __init__(self, name: str, method: str, path: str, payload: str) -> None:
        self.name = name
        self.method = method
        self.path = path
        self.payload = payload

    def __str__(self):
        return '{}: {} {}\n{}'.format(self.name, self.method, self.path, self.payload)


class MockServer:
    """Small mock HTTP server"""
    @staticmethod
    def ProvideMockHandler(server):
        class MockHandler(http.server.BaseHTTPRequestHandler):
            def __init__(self, *args, **kwargs) -> None:
                self.mock_server = server
                super(MockHandler, self).__init__(*args, **kwargs)

            def log_message(self, format: str, *args: Any) -> None:
                pass

            def handle_mock(self, method: str, path: str, payload: str):
                mock = self.mock_server.get_mock(method, path, payload)
                if mock:
                    code, payload = mock.get_response()
                    self.send_response(code)
                    if payload:
                        self.send_header('content-length',
                                         len(payload))
                        self.end_headers()
                        self.wfile.write(payload)
                    else:
                        self.end_headers()
                else:
                    self.send_error(404)

            def do_GET(self):
                (_, _, path, _, query, _) = parse.urlparse(self.path)
                self.handle_mock('GET', path, query)

            def do_POST(self):
                (_, _, path, _, _, _) = parse.urlparse(self.path)
                payload = self.rfile.read(int(self.headers['content-length']))
                self.handle_mock('GET', path, payload.decode('utf-8'))

        return MockHandler

    def __init__(self, port) -> None:
        self.httpd = http.server.HTTPServer(
            ('', port), MockServer.ProvideMockHandler(self))

        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.start()
        self.reset_mocks()

    def shutdown(self):
        """Shuts down the mock server"""
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()

    def get_mock(self, method: str, path: str, payload: str) -> MockResponse:
        """Return the first mock that matches the query and register the query"""
        res_name = '__none__'
        res_mock = None
        for name, mock in self.mocks.items():
            if mock.match(method, path):
                res_name = name
                res_mock = mock
                break
        self.register_query(res_name, method, path, payload)
        return res_mock

    def reset_mocks(self):
        """To be called at the end of a test. Forgets all the mocks and the queries it received"""
        self.mocks: Dict[str, MockResponse] = {}
        self.queries: List[MockQuery] = []

    def register_query(self, name: str, method: str, path: str, payload: str):
        """to keep track of queries made to the server"""
        self.queries.append(
            MockQuery(name, method, path, payload))

    def add_mock(self, name: str, mock: MockResponse):
        """To add a mock response. The first Mock to match a query will be used"""
        self.mocks[name] = mock
