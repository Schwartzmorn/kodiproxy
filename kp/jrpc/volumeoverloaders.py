import json
from kp.avreceiver import AVReceiver
from kp.jrpc.jrpcserver import JRPCOverloader, JRPCServer, JRPCOverloaderWithHandler
import numbers


class JRPCAVReceiverOverloader(JRPCOverloaderWithHandler):
    def __init__(self, server: JRPCServer, receiver: AVReceiver):
        super().__init__(server)
        self.receiver = receiver


class SetVolumeOverloader(JRPCAVReceiverOverloader):
    def __init__(self, receiver: AVReceiver):
        super().__init__(None, receiver)

    def overload_query(self, params):
        volume = params['volume']
        if isinstance(volume, numbers.Number):
            volume = self.receiver.set_volume(params['volume'])
        elif volume == 'increment':
            volume = self.receiver.incr_volume(True)
        elif volume == 'decrement':
            volume = self.receiver.incr_volume(False)
        else:
            return 400, 'Invalid volume value: {}'.format(volume), None
        return 200, volume, None


class SetMuteOverloader(JRPCAVReceiverOverloader):
    def __init__(self, receiver: AVReceiver):
        super().__init__(None, receiver)

    def overload_query(self, params):
        mute = params['mute']
        if mute == 'toggle':
            mute = not self.receiver.get_mute()
        elif not isinstance(mute, bool):
            raise ValueError('Invalid mute value: {}'.format(mute))
        mute = self.receiver.set_mute(mute)
        return 200, mute, None


class GetPropertiesOverloader(JRPCAVReceiverOverloader):
    _AVR_PROPERTIES = {'volume', 'muted'}

    def __init__(self, server: JRPCServer, receiver: AVReceiver):
        super().__init__(server, receiver)

    def overload_query(self, params):
        params = set(params['properties'])
        avr_properties = GetPropertiesOverloader._AVR_PROPERTIES.intersection(
            params)
        other_properties = params - GetPropertiesOverloader._AVR_PROPERTIES
        res = dict()
        if avr_properties:
            volume, muted = self.receiver.get_volume()
            for prop in avr_properties:
                if prop == 'muted':
                    res[prop] = muted
                elif prop == 'volume':
                    res[prop] = volume
        if other_properties:
            _, payload, _ = self.forward('Application.GetProperties', {
                'properties': list(other_properties)})

            payload = json.loads(payload)
            res.update(payload['result'])

        return 200, res, None
