# -*- coding: utf-8 -*-

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import os
import tempfile

# Import Salt Libs
from salt.cloud.clouds import ec2
from salt.exceptions import SaltCloudSystemExit

# Import Salt Testing Libs
from tests.support.unit import TestCase, skipIf
from tests.support.mock import NO_MOCK, NO_MOCK_REASON, patch, PropertyMock
from tests.support.paths import TMP
from tests.unit.test_crypt import PRIVKEY_DATA

import mock

PASS_DATA = (
    b'qOjCKDlBdcNEbJ/J8eRl7sH+bYIIm4cvHHY86gh2NEUnufFlFo0gGVTZR05Fj0cw3n/w7gR'
    b'urNXz5JoeSIHVuNI3YTwzL9yEAaC0kuy8EbOlO2yx8yPGdfml9BRwOV7A6b8UFo9co4H7fz'
    b'DdScMKU2yzvRYvp6N6Q2cJGBmPsemnXWWusb+1vZVWxcRAQmG3ogF6Z5rZSYAYH0N4rqJgH'
    b'mQfzuyb+jrBvV/IOoV1EdO9jGSH9338aS47NjrmNEN/SpnS6eCWZUwwyHbPASuOvWiY4QH/'
    b'0YZC6EGccwiUmt0ZOxIynk+tEyVPTkiS0V8RcZK6YKqMWHpKmPtLBzfuoA=='
)


@skipIf(NO_MOCK, NO_MOCK_REASON)
class EC2TestCase(TestCase):
    '''
    Unit TestCase for salt.cloud.clouds.ec2 module.
    '''

    def setUp(self):
        with tempfile.NamedTemporaryFile(dir=TMP, suffix='.pem', delete=True) as fp:
            self.key_file = fp.name

    def tearDown(self):
        if os.path.exists(self.key_file):
            os.remove(self.key_file)

    def test__validate_key_path_and_mode(self):

        # Key file exists
        with patch('os.path.exists', return_value=True):
            with patch('os.stat') as patched_stat:

                type(patched_stat.return_value).st_mode = PropertyMock(return_value=0o644)
                self.assertRaises(
                    SaltCloudSystemExit, ec2._validate_key_path_and_mode, 'key_file')

                type(patched_stat.return_value).st_mode = PropertyMock(return_value=0o600)
                self.assertTrue(ec2._validate_key_path_and_mode('key_file'))

                type(patched_stat.return_value).st_mode = PropertyMock(return_value=0o400)
                self.assertTrue(ec2._validate_key_path_and_mode('key_file'))

        # Key file does not exist
        with patch('os.path.exists', return_value=False):
            self.assertRaises(
                SaltCloudSystemExit, ec2._validate_key_path_and_mode, 'key_file')

    @mock.patch('salt.cloud.clouds.ec2._get_node')
    @mock.patch('salt.cloud.clouds.ec2.get_location')
    @mock.patch('salt.cloud.clouds.ec2.get_provider')
    @mock.patch('salt.utils.aws.query')
    def test_get_password_data(self, query, get_provider, get_location, _get_node):
        query.return_value = [
            {
            'passwordData': PASS_DATA
            }
        ]
        _get_node.return_value = {'instanceId': 'i-abcdef'}
        get_location.return_value = 'us-west2'
        get_provider.return_value = 'ec2'
        ec2.__opts__ = {}
        ec2.__active_provider_name__ = None
        with open(self.key_file, 'w') as fp:
            fp.write(PRIVKEY_DATA)
        ret = ec2.get_password_data(
            name='i-abcddef', kwargs={'key_file': self.key_file}, call='action'
        )
        assert ret['passwordData'] == PASS_DATA
        assert ret['password'] == b'testp4ss!'
