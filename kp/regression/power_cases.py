from kp.regression.regression_case import RegressionCase


class PowerCase(RegressionCase):
    def test_get_properties(self):
        """Check that we say we can only reboot"""
        code, res = self.open_jrpc('System.GetProperties', {'properties': [
            'canshutdown', 'cansuspend', 'canhibernate', 'canreboot']})

        self.assertEqual(code, 200)
        self.assertPayloadEqual(res, {
            'canshutdown': False, 'cansuspend': False, 'canhibernate': False, 'canreboot': True
        })
