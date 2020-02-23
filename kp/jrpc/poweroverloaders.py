from kp.jrpc.jrpcserver import JRPCOverloader, JRPCOverloaderWithHandler
from kp.avreceiver import AVReceiver
from kp.jrpc.volumeoverloaders import JRPCAVReceiverOverloader
from kp.types import Response


class SuspendOverloader(JRPCOverloader):
    """Class to intercept queries to shut down Kodi"""

    def overload_query(self, params) -> Response:
        """Does nothing, we are not able to recover from the pi shutting down"""
        return 200, 'OK', None


class SystemPropertiesOverloader(JRPCOverloader):
    """Overrides what the Kodi is supposed to be able to do in terms of powering off etc."""

    def overload_query(self, params) -> Response:
        res = dict()
        for key in params['properties']:
            res[key] = key == 'canreboot'
        return 200, res, None


class ApplicationQuitOverloader(JRPCAVReceiverOverloader):
    """Class to intercept queries quit Kodi"""

    def __init__(self, receiver: AVReceiver):
        super().__init__(None, receiver)

    def overload_query(self, params) -> Response:
        # ask for the receiver to shut down
        # TODO
        return 200, 'OK', None
