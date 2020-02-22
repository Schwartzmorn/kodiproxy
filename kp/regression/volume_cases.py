from kp.regression.regression_case import RegressionCase
from kp.regression.mock_server import MockResponse


class VolumeCase(RegressionCase):
    FULL_STATUS = b"""<?xml version="1.0" encoding="utf-8" ?>
<item>
<Zone><value>MainZone</value></Zone>
<Power><value>STANDBY</value></Power>
<Model><value></value></Model>
<InputFuncSelect><value>AUXB</value></InputFuncSelect>
<MasterVolume><value>-35.0</value></MasterVolume>
<Mute><value>on</value></Mute>
</item>"""

    VOLUME_STATUS = b"""<?xml version="1.0" encoding="utf-8" ?>
<item>
<MasterVolume><value>-35.0</value></MasterVolume>
<Mute><value>off</value></Mute>
</item>"""

    def test_set_volume(self):
        """Setting the volume targets the receiver"""
        self.receiver_mock.add_mock('volumeset', MockResponse(responses=[
            (200, VolumeCase.VOLUME_STATUS)
        ], path='/goform/formiPhoneAppVolume.xml'))

        code, payload = self.open_jrpc('Application.SetVolume', {'volume': 66})

        self.assertEqual(code, 200)
        self.assertPayloadEqual(payload, 75)
        self.assertEqual(self.receiver_mock.queries[0].payload, '1+-40.0')

    def test_incr_volume(self):
        """Incrementing the volume targets the receiver"""
        self.receiver_mock.add_mock('volume', MockResponse(
            responses=[(200, VolumeCase.VOLUME_STATUS)],
            path='/goform/formiPhoneAppVolume.xml'
        ))
        self.receiver_mock.add_mock('status', MockResponse(
            responses=[(200, VolumeCase.FULL_STATUS)],
            path='/goform/formMainZone_MainZoneXmlStatus.xml'
        ))

        code, payload = self.open_jrpc(
            'Application.SetVolume', {'volume': 'increment'})

        self.assertEqual(code, 200)
        self.assertPayloadEqual(payload, 75)
        self.assertEqual(self.receiver_mock.queries[1].payload, '1+-34.0')

    def test_get_properties_volume(self):
        """Getting the volume properties queries the receiver"""
        self.receiver_mock.add_mock('status', MockResponse(
            responses=[(200, VolumeCase.FULL_STATUS)],
            path='/goform/formMainZone_MainZoneXmlStatus.xml'
        ))

        code, payload = self.open_jrpc('Application.GetProperties', {
                                       'properties': ['volume', 'muted']})

        self.assertEqual(code, 200)
        self.assertPayloadEqual(payload, {'muted': True, 'volume': 75})

        self.assertEqual(len(self.jrpc_mock.queries), 0)

    def test_get_properties_other(self):
        """Getting the other properties targets the jrpc server"""
        self.jrpc_mock.add_mock('properties', MockResponse(
            responses=[(200, b'{"result": {"prop1": "value", "prop2": 34 } }')], path='/jsonrpc'))

        code, payload = self.open_jrpc('Application.GetProperties', {
                                       'properties': ['prop1', 'prop2']})

        self.assertEqual(code, 200)
        self.assertPayloadEqual(payload, {'prop1': "value", 'prop2': 34})

        self.assertEqual(len(self.receiver_mock.queries), 0)
