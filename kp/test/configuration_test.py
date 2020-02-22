from kp.confbase import KPConfBase
import unittest


class TestKPConfBase(unittest.TestCase):
    _DEFAULT_CONFIGURATION = {
        'key1': 1,
        'key2': 'value'
    }

    def test_default(self):
        '''If no value is given, we return the default'''
        conf = KPConfBase(TestKPConfBase, None)

        self.assertEqual(conf.key1, 1)
        self.assertEqual(conf.key2, 'value')
        self.assertEqual(conf.default_key2, 'value')
        with self.assertRaises(AttributeError):
            conf.key3

    def test_value(self):
        '''The configuration overrides the default'''
        conf = KPConfBase(TestKPConfBase, {
            'key2': 'new_value'
        })

        self.assertEqual(conf.key2, 'new_value')
        self.assertEqual(conf.default_key2, 'value')
