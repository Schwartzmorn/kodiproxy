import logging
import time
from typing import Optional
from urllib import request
import xml.etree.ElementTree as ET


class AVStatus:
    def __init__(self, tree: ET.Element):
        self.input = None
        self.mute = None
        self.power = None
        self.volume = None
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
    _MIN_VOLUME = -80.0
    _MAX_VOLUME = -20.0

    _POWER = 'formiPhoneAppPower.xml?1+Power'
    _SOURCE = 'formiPhoneAppDirect.xml?SI'
    _VOLUME = 'formiPhoneAppVolume.xml?1+{:.1f}'
    _VOLUME_MUTE = 'formiPhoneAppMute.xml?1+Mute'

    def __init__(self, conf):
        if conf.port:
            address = '{}:{}'.format(conf.ip, conf.port)
        else:
            address = conf.ip
        self.address = 'http://{}/goform/'.format(address)
        self.desired_input = conf.desiredInput

    def _send_command(self, command: str) -> AVStatus:
        res = request.urlopen(self.address + command, timeout=5).read()
        tree = ET.fromstring(res)
        return AVStatus(tree)

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
        volume -= AVReceiver._MIN_VOLUME
        volume /= AVReceiver._MAX_VOLUME - AVReceiver._MIN_VOLUME
        return int(volume * 100)

    def _percent_to_db(self, volume: int) -> float:
        volume = float(volume) / 100
        volume *= AVReceiver._MAX_VOLUME - AVReceiver._MIN_VOLUME
        # even though we want a float, we want it to take an integer value
        return float(int(volume + AVReceiver._MIN_VOLUME))

    def get_power(self) -> bool:
        return self._get_status().power

    def set_power(self, onOff: bool) -> bool:
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
            return status.power

    def get_mute(self) -> bool:
        return self._get_status().mute

    def set_mute(self, mute: bool) -> bool:
        return self._send_command(
            AVReceiver._VOLUME_MUTE + ('On' if mute else 'Off')).mute

    def incr_volume(self, incr: bool) -> int:
        # works better than using the actual commands to increase/decrease
        volume = self._get_status().volume
        if volume == '--':  # why ?
            volume = AVReceiver._MIN_VOLUME
        volume = volume + (1 if incr else -1)
        volume = max(AVReceiver._MIN_VOLUME, min(
            volume, AVReceiver._MAX_VOLUME))
        return self._db_to_percent(
            self._send_command(AVReceiver._VOLUME.format(volume)).volume)

    def get_volume(self) -> int:
        return self._db_to_percent(self._get_status().volume)

    def set_volume(self, volume: int) -> int:
        volume = self._percent_to_db(volume)
        return self._db_to_percent(
            self._send_command(AVReceiver._VOLUME.format(volume)).volume)


if __name__ == "__main__":
    from configuration import KPConfiguration
    conf = KPConfiguration('../kodiproxy.json')
    receiver = AVReceiver(conf.receiver)
    print(receiver.set_power(True))
