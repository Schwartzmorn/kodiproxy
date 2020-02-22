from kp import avreceiver
import unittest
from unittest.mock import call, patch, MagicMock


conf_mock = {
    'desiredInput': 'DINP',
    'ip': 'the_host',
    'port': 666,
    'minVolume': -80,
    'maxVolume': -20
}


class MockStatus:
    def __init__(self, inp=None, mute=None, power=None, volume=None):
        self.input = inp
        self.mute = mute
        self.power = power
        self.volume = volume


class TestAVStatus(unittest.TestCase):
    def test_full_status(self):
        '''Decoding of the response to the get status command'''
        status = avreceiver.AVStatus(
            b"""<?xml version="1.0" encoding="utf-8" ?>
            <item>
            <Zone><value>MainZone</value></Zone>
            <Power><value>STANDBY</value></Power>
            <Model><value></value></Model>
            <InputFuncSelect><value>AUXB</value></InputFuncSelect>
            <MasterVolume><value>--</value></MasterVolume>
            <Mute><value>off</value></Mute>
            </item>""")

        self.assertEqual(status.input, 'AUXB')
        self.assertEqual(status.mute, False)
        self.assertEqual(status.power, False)
        self.assertEqual(status.volume, '--')

        status = avreceiver.AVStatus(
            b"""<?xml version="1.0" encoding="utf-8" ?>
            <item>
            <Zone><value>MainZone</value></Zone>
            <Power><value>ON</value></Power>
            <Model><value></value></Model>
            <InputFuncSelect><value>NET</value></InputFuncSelect>
            <MasterVolume><value>-70.0</value></MasterVolume>
            <Mute><value>on</value></Mute>
            </item>""")

        self.assertEqual(status.input, 'NET')
        self.assertEqual(status.mute, True)
        self.assertEqual(status.power, True)
        self.assertEqual(status.volume, -70)

    def test_partial_status(self):
        '''Decoding of status when the response is partial'''
        status = avreceiver.AVStatus(
            b"""<?xml version="1.0" encoding="utf-8" ?>
            <item>
            <MasterVolume><value>-60.0</value></MasterVolume>
            <Mute><value>off</value></Mute>
            </item>""")

        self.assertIsNone(status.input)
        self.assertEqual(status.mute, False)
        self.assertIsNone(status.power)
        self.assertEqual(status.volume, -60)


class TestAVReceiver(unittest.TestCase):
    def check_int(self, value, expected: int):
        self.assertIsInstance(value, int)
        self.assertEqual(value, expected)

    def check_float(self, value, expected: float):
        self.assertIsInstance(value, float)
        self.assertEqual(value, expected)

    def test_volume_transform(self):
        '''Volume translation from receiver to percentage'''
        receiver = avreceiver.AVReceiver(conf_mock)

        self.check_int(receiver._db_to_percent('--'), 0)
        self.check_int(receiver._db_to_percent(-65.0), 25)
        self.check_int(receiver._db_to_percent(conf_mock['maxVolume']), 100)

        self.check_float(receiver._percent_to_db(0), conf_mock['minVolume'])
        self.check_float(receiver._percent_to_db(25), -65)
        self.check_float(receiver._percent_to_db(100), conf_mock['maxVolume'])

    @patch('avreceiver.request.urlopen')
    def test_send_command(self, mock: MagicMock):
        '''Test internal send command method'''
        receiver = avreceiver.AVReceiver(conf_mock)

        mock.return_value.read.return_value = b'''<?xml version="1.0" encoding="utf-8" ?>
            <item>
            <Zone><value>MainZone</value></Zone>
            <Power><value>ON</value></Power>
            <Model><value></value></Model>
            <InputFuncSelect><value>NET</value></InputFuncSelect>
            <MasterVolume><value>-70.0</value></MasterVolume>
            <Mute><value>on</value></Mute>
            </item>'''

        status = receiver._send_command('someurl')

        mock.assert_called_once_with(
            'http://{}:{}/goform/someurl'.format(conf_mock['ip'], conf_mock['port']), timeout=5)

        self.assertEqual(status.volume, -70)

    def test_incr_volume(self):
        '''Correctly increment the volume'''
        receiver = avreceiver.AVReceiver(conf_mock)

        receiver._send_command = MagicMock()
        receiver._send_command.side_effect = [
            MockStatus(volume=-36), MockStatus(volume=-35)]

        volume = receiver.incr_volume(True)

        self.assertEqual(volume, 75)
        receiver._send_command.assert_has_calls([
            call('formMainZone_MainZoneXmlStatus.xml'),
            call('formiPhoneAppVolume.xml?1+-35.0')
        ])

    def test_incr_volume_max(self):
        '''Cannot exceed maximum volume'''
        receiver = avreceiver.AVReceiver(conf_mock)

        receiver._send_command = MagicMock()
        receiver._send_command.side_effect = [
            MockStatus(volume=conf_mock['maxVolume']), MockStatus(volume=conf_mock['maxVolume'])]

        volume = receiver.incr_volume(True)

        self.assertEqual(volume, 100)
        receiver._send_command.assert_called_with(
            'formiPhoneAppVolume.xml?1+-20.0')

    def test_decr_volume_min(self):
        '''Cannot go below minimum volume'''
        receiver = avreceiver.AVReceiver(conf_mock)

        receiver._send_command = MagicMock()
        receiver._send_command.side_effect = [
            MockStatus(volume=conf_mock['minVolume']), MockStatus(volume='--')]

        volume = receiver.incr_volume(False)

        self.assertEqual(volume, 0)
        receiver._send_command.assert_called_with(
            'formiPhoneAppVolume.xml?1+-80.0')

    def test_set_volume(self):
        '''Setting volume works and does not exceed boundaries'''
        receiver = avreceiver.AVReceiver(conf_mock)
        receiver._send_command = MagicMock()
        receiver._send_command.return_value = MockStatus(
            volume=conf_mock['maxVolume'])

        # For this test, we also check that we return the volume
        self.assertEqual(receiver.set_volume(25), 100)
        receiver.set_volume(200)
        receiver.set_volume(-50)

        receiver._send_command.assert_has_calls([
            call('formiPhoneAppVolume.xml?1+-65.0'),
            call('formiPhoneAppVolume.xml?1+-20.0'),
            call('formiPhoneAppVolume.xml?1+-80.0')
        ])

    @patch('avreceiver.request.urlopen')
    @patch('avreceiver.time.sleep')
    def test_power_on(self, mock_sleep: MagicMock, mock_open: MagicMock):
        '''When asked to be switched on, we send the command 
        to turn on, then try to set the input until successful'''
        receiver = avreceiver.AVReceiver(conf_mock)

        receiver._send_command = MagicMock()
        receiver._send_command.side_effect = [
            MockStatus(power=False, inp='NET'),
            MockStatus(power=False),
            MockStatus(inp='NET'),
            MockStatus(inp='NET'),
            MockStatus(inp='NET'),
            MockStatus(inp=conf_mock['desiredInput'])
        ]

        res = receiver.set_power(True)

        receiver._send_command.assert_has_calls([
            call('formMainZone_MainZoneXmlStatus.xml'),
            call('formiPhoneAppPower.xml?1+PowerOn'),
            call('formMainZone_MainZoneXmlStatus.xml'),
            call('formMainZone_MainZoneXmlStatus.xml'),
            call('formMainZone_MainZoneXmlStatus.xml'),
            call('formMainZone_MainZoneXmlStatus.xml')
        ])

        self.assertEqual(mock_sleep.call_count, 4)
        self.assertEqual(mock_open.call_count, 4)
        mock_open.assert_any_call(
            'http://{}:{}/goform/formiPhoneAppDirect.xml?SI{}'.format(
                conf_mock['ip'], conf_mock['port'], conf_mock['desiredInput']),
            timeout=5)

        self.assertEqual(res, True)

    def test_power_off(self):
        '''Power off the receiver'''
        receiver = avreceiver.AVReceiver(conf_mock)

        receiver._send_command = MagicMock()
        receiver._send_command.return_value = MockStatus(
            inp=conf_mock['desiredInput'], power=True)

        res = receiver.set_power(False)

        receiver._send_command.assert_has_calls([
            call('formMainZone_MainZoneXmlStatus.xml'),
            call('formiPhoneAppPower.xml?1+PowerStandby')
        ])

        self.assertEqual(res, False)

    def test_power_off_wrong_input(self):
        '''We don't power off when the receiver is on the wrong input'''
        receiver = avreceiver.AVReceiver(conf_mock)

        receiver._send_command = MagicMock()
        receiver._send_command.return_value = MockStatus(
            inp='NET', power=True)

        res = receiver.set_power(False)

        receiver._send_command.assert_called_once_with(
            'formMainZone_MainZoneXmlStatus.xml')

        self.assertEqual(res, False)
