#
# ============LICENSE_START==========================================
# org.onap.vvp/engagementmgr
# ===================================================================
# Copyright © 2017 AT&T Intellectual Property. All rights reserved.
# ===================================================================
#
# Unless otherwise specified, all software contained herein is licensed
# under the Apache License, Version 2.0 (the “License”);
# you may not use this software except in compliance with the License.
# You may obtain a copy of the License at
#
#             http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
#
# Unless otherwise specified, all documentation contained herein is licensed
# under the Creative Commons License, Attribution 4.0 Intl. (the “License”);
# you may not use this documentation except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://creativecommons.org/licenses/by/4.0/
#
# Unless required by applicable law or agreed to in writing, documentation
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ============LICENSE_END============================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.
from engagementmanager.utils.constants import Constants
from validationmanager.rados.rgwa_client import _validate_args, RGWAClient


try:
    from unittest.mock import patch, ANY
except ImportError:
    from mock import patch, ANY

try:
    from unittest import assertRaises, expectedFailure
except ImportError:
    from pytest import raises as assertRaises
    from pytest import mark
    expectedFailure = mark.xfail


class Test_ValidateArgs(object):

    def setup(self):
        self.valid_args = {
            'foo': ['foo1', 'foo2'],
            'bar': [1, 2, 3],
        }

    def test_unconstrained(self):
        _validate_args(self.valid_args, baz="quux")

    def test_none_value(self):
        _validate_args(self.valid_args, foo=None)

    def test_good_value(self):
        _validate_args(self.valid_args, foo="foo1")

    def test_bad_value_raises(self):
        with assertRaises(ValueError):
            _validate_args(self.valid_args, foo="foo3")


@patch('ice_rgwa_client.request')
class TestRGWAClientMethods(object):
    """Tests that all the methods invoke requests.request() with the
    appropriate arguments.

    """

    def setup(self):
        self.access_key = 'ABCDEFGHIJKLMNOPQRST'
        self.secret_key = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn'
        self.conn = RGWAClient(
            access_key=self.access_key,
            secret_key=self.secret_key,
            base_url=Constants.rgwa_base_url
        )

    def test_get_usage(self, r):
        self.conn.get_usage(uid='foo', show_entries=True)
        r.assert_called_once_with(
            auth=ANY,
            method='get',
            json={},
            params={'show-entries': True, 'show-summary': False, 'uid': 'foo'},
            url=Constants.rgwa_base_url + '/usage',
            verify=True,
        )

    def test_trim_usage(self, r):
        self.conn.trim_usage(uid='foo', remove_all=True)
        r.assert_called_once_with(
            auth=ANY,
            method='delete',
            json={},
            params={'remove-all': True, 'uid': 'foo'},
            url='http://localhost:8123/admin/usage',
            verify=True,
        )

    def test_get_user(self, r):
        self.conn.get_user(uid='foo')
        r.assert_called_once_with(
            auth=ANY,
            method='get',
            json={},
            params={'uid': 'foo'},
            url=Constants.rgwa_base_url + '/user',
            verify=True,
        )

    # Marked FIXME because we experience diminishing returns here. All the
    # methods in the library are basically one-liner calls to the common
    # _request method, which has been sufficiently covered. There's no
    # additional business logic that would be tested, only ensuring beyond api
    # stability.  Time would be better spent figuring out how to get tox to
    # stand up testing instances of various versions of an actual radosgw
    # server for integration testing.

    @expectedFailure
    def test_create_user(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_modify_user(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_remove_user(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_create_subuser(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_modify_subuser(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_remove_subuser(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_create_key(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_remove_key(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_get_bucket(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_check_bucket_index(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_remove_bucket(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_unlink_bucket(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_link_bucket(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_remove_object(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_get_policy(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_add_capability(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_remove_capability(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_get_quota(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_set_quota(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_get_user_quota(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_set_user_quota(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_get_user_bucket_quota(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_set_user_bucket_quota(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_get_users(self, r):
        raise NotImplementedError  # FIXME

    @expectedFailure
    def test_get_buckets(self, r):
        raise NotImplementedError  # FIXME


# FIXME TODO Add integration tests against a local ceph radosgw instance,
# (disabled by default). Record result of test suite in repository.
