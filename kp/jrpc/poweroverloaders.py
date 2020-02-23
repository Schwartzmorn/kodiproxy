from kp.avreceiver import AVReceiver
from kp.cecclient import CECClient
from kp.jrpc.jrpcserver import JRPCOverloader, JRPCOverloaderWithHandler
from kp.jrpc.volumeoverloaders import JRPCAVReceiverOverloader
from kp.types import Response


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
        self.cecclient = CECClient()

    def overload_query(self, params) -> Response:
        self.receiver.set_power(False)
        self.cecclient.switch_off()
        return 200, 'OK', None
