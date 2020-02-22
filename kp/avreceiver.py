from kp.confbase import KPConfBase
import logging
import time
from typing import Optional, Tuple
from urllib import request
import xml.etree.ElementTree as ET

LOGGER = logging.getLogger('kodiproxy')


class AVStatus:
    """Holds the status of the AV receiver. Might not be complete depending on where it came from."""

    def __init__(self, response: bytes):
        self.input = None
        self.mute = None
        self.power = None
        self.volume = None
        tree = ET.fromstring(response)
        for element in tree.iter():
            if element.tag == 'Power':
                self.power = element.find('value').text == 'ON'
            elif element.tag == 'InputFuncSelect':
                self.input = element.find('value').text
            elif element.tag == 'MasterVolume':
                volume = element.find('value').text
                self.volume = volume if volume == '--' else float(volume)
            elif element.tag == 'Mute':
                self.mute = element.find('value').text == 'on'

    def __str__(self) -> str:
        return 'Power: {}\nInput: {}\nVolume: {}\nMute: {}'.format(
            self.power, self.input, self.volume, self.mute)


class AVReceiver:
    """Wraps the interface of the AV receiver"""
    _POWER = 'formiPhoneAppPower.xml?1+Power'
    _SOURCE = 'formiPhoneAppDirect.xml?SI'
    _VOLUME = 'formiPhoneAppVolume.xml?1+{:.1f}'
    _VOLUME_MUTE = 'formiPhoneAppMute.xml?1+Mute'

    _DEFAULT_CONFIGURATION = {
        'desiredInput': 'AUXB',
        'ip': None,
        'port': None,
        'minVolume': -80,
        'maxVolume': -20
    }

    def __init__(self, conf):
        conf = KPConfBase(AVReceiver, conf)
        LOGGER.info('Receiver configuration:\n%s', conf)
        if conf.port:
            address = '{}:{}'.format(conf.ip, conf.port)
        else:
            address = conf.ip
        self.address = 'http://{}/goform/'.format(address)
        self.desired_input = conf.desiredInput
        self.min_volume = conf.minVolume
        self.max_volume = conf.maxVolume

    def _send_command(self, command: str) -> AVStatus:
        res = request.urlopen(self.address + command, timeout=5).read()
        return AVStatus(res)

    def _get_status(self) -> AVStatus:
        return self._send_command('formMainZone_MainZoneXmlStatus.xml')

    def _set_source(self) -> bool:
        # of course we don't get the source in response
        request.urlopen(self.address + AVReceiver._SOURCE +
                        self.desired_input, timeout=5)
        return self._get_status()

    def _db_to_percent(self, volume: [float, str]) -> int:
        if volume == '--':  # I hate you
            return 0
        volume -= self.min_volume
        volume /= self.max_volume - self.min_volume
        return int(volume * 100)

    def _percent_to_db(self, volume: int) -> float:
        volume = float(volume) / 100
        volume *= self.max_volume - self.min_volume
        # even though we want a float, we want it to take an integer value
        return float(int(volume + self.min_volume))

    def get_power(self) -> bool:
        """Returns whether the AV receiver is up or not"""
        status = self._get_status()
        return status.power and status.input == self.desired_input

    def set_power(self, onOff: bool) -> bool:
        """Power on or off the AV receiver.

        If onOff is True, it will power on the receiver on and swicth to the desired input.

        If onOff is False, it will power off the receiver if it is currently on the desired input"""
        status = self._get_status()
        if onOff:
            if not status.power:
                self._send_command(AVReceiver._POWER + 'On')
            i = 8  # arbitrary number of retries, 4 is usually enough
            while status.input != self.desired_input and i > 0:
                time.sleep(0.5)
                status = self._set_source()
                i -= 1
            return True
        else:
            if status.input == self.desired_input:
                status = self._send_command(AVReceiver._POWER + 'Standby')
            return False

    def get_mute(self) -> bool:
        """Returns whether the receiver is muted or not"""
        return self._get_status().mute

    def set_mute(self, mute: bool) -> bool:
        """Mutes or unmutes the receiver"""
        return self._send_command(
            AVReceiver._VOLUME_MUTE + ('On' if mute else 'Off')).mute

    def incr_volume(self, incr: bool) -> int:
        """Increases or decreases the volume"""
        # setting the volume works better than using the actual
        # commands to increase/decrease
        volume = self._get_status().volume
        if volume == '--':  # why ?
            volume = self.min_volume
        volume = volume + (1 if incr else -1)
        volume = max(self.min_volume, min(
            volume, self.max_volume))
        return self._db_to_percent(
            self._send_command(AVReceiver._VOLUME.format(volume)).volume)

    def get_volume(self) -> Tuple[int, bool]:
        """Returns the volume in percentage and the mute status"""
        status = self._get_status()
        return self._db_to_percent(status.volume), status.mute

    def set_volume(self, volume: int) -> int:
        """Sets the volume in percentage"""
        volume = max(0, min(volume, 100))
        volume = self._percent_to_db(volume)
        return self._db_to_percent(
            self._send_command(AVReceiver._VOLUME.format(volume)).volume)
