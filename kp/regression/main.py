from kp.main import setup_and_start
from kp.regression.mock_server import MockServer
from kp.regression.regression_case import RegressionCase
from kp.regression.power_cases import PowerCase
from kp.regression.volume_cases import VolumeCase
from kp.server import KodiProxyServer
import sys
import threading
import traceback
import unittest
from urllib.request import urlopen


def get_suite(testClass) -> unittest.TestSuite:
    return unittest.TestLoader().loadTestsFromTestCase(testClass)


def main_regression() -> int:
    RegressionCase.JRPC_MOCK = MockServer(43211)
    RegressionCase.RECEIVER_MOCK = MockServer(43212)
    event = threading.Event()
    server_thread = threading.Thread(target=setup_and_start, args=[
        'kp/regression/kodiproxy_reg.json', event])
    server_thread.start()

    event.wait()

    return_code = 0

    try:
        suite = unittest.TestSuite()
        suite.addTests(map(get_suite, [PowerCase, VolumeCase]))

        runner = unittest.TextTestRunner(verbosity=2)
        res = runner.run(suite)
        return_code = 0 if res.wasSuccessful() else 1
    except:
        print('Uncaught error while running tests')
        print(traceback.format_exc())
        return_code = 2

    # asks the server to shut down
    urlopen('http://localhost:43210/quit')

    RegressionCase.JRPC_MOCK.shutdown()
    RegressionCase.RECEIVER_MOCK.shutdown()

    server_thread.join()
    return return_code
