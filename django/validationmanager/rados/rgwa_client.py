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
"""A Ceph Rados Gateway Admin Operations API client."""

# Design goals:
#
# - Minimal abstractions over the raw Requests calls
# - Python method signatures enforce optional/required API parameters
# - DRY by procedurally mapping kwargs to API parameters
# - (TODO) procedurally generate this library directly from Ceph docs

import os

from awsauth import S3Auth
from requests import request


def _validate_args(valid_args, **kwargs):
    """Validate kwargs conforms to a specification of allowable values.

    Ensures that any keyword arguments either:
    - are unconstrained by valid_args, or
    - have a value of None, or
    - have a value that matches one of the corresponding specified values.

    This is useful for limiting several common keyword arguments to a set of
    values across many methods, while ignoring those set to None. (Typically,
    these are optional and were unspecified by the caller.)

    This is a validator function: it either returns None on success, or raises
    an exception on failure.

    """
    for keyword, value in kwargs.items():
        if keyword not in valid_args:
            continue
        if value is None:
            continue
        if value in valid_args[keyword]:
            continue
        raise ValueError(
            "Invalid parameter {:s}={!r}; must be one of: {!r}".format(
                keyword, value, valid_args[keyword]))


class RGWAClient(object):
    """A client for the Ceph Rados Gateway Admin Operations API.

    This class is implemented as a simplistic/mechanical wrapper around the
    Python Requests library. Calling its methods triggers HTTP(S) calls to the
    specified API endpoint, and the responses are decoded from JSON to Python
    objects before being returned.

    The methods available on this object should mirror the endpoints of the API
    closely enough that its documentation may be used as a reference:

    http://docs.ceph.com/docs/master/radosgw/adminops/

    """
    valid_args = {
        'quota_type': ['user', 'bucket'],
        'key_type': ['s3', 'swift'],
    },

    def __init__(self, base_url, access_key=None, secret_key=None,
                 verify='/etc/ssl/certs/ca-certificates.crt',
                 return_raw_response=False):
        """

        base_url (string):

            The full URL to your admin entry point. Should include the protocol
            ("http://" or "https://"), and optionally the port as well. The
            URL-path to the admin entry point is configurable using "rgw admin
            entry" in your Ceph configuration. Example:

                "https://s3.example.com:8080/admin"

        access_key (string): Your AWS Access Key ID
        secret_key (string): Your AWS Secret Access Key

            If either of access_key or secret_key are omitted, this class will
            attempt to look the values in the environment variables
            AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY respectively.

        verify (boolean):

            Set to False to disable SSL Certificate verification, or optionally
            set to the path to a CA Certificate bundle. This is passed directly
            to the underlying call to the requests library; see:
            http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification

        return_raw_response (boolean):

            All of the methods of this class return, upon success, the objects
            resulting from parsing the JSON data returned by the API. On error,
            they raise an exception. This is meant for caller convenience, but
            may be undesirable in some situations because callers have no
            access to the additional data and methods available in the raw
            Response object.

                from ice_rgwa_client import (
                    RGWAClient, HTTPError)
                # ...
                rgw = RGWAClient(
                    access_key='...',
                    secret_key='...',
                    base_url='...',
                    )
                # ...
                try:
                    user = rgw.get_user('nonexistent')
                except HTTPError as exc:
                    if exc.response.status_code == 404:
                        print("No such user")
                        continue
                    else:
                        print("Problem loading user")
                        raise

            If return_raw_response is set to True, the methods will instead
            return the raw Response object from the Requests library, and it
            will be up to the caller to check the error status as needed.

            See
            http://docs.python-requests.org/en/master/user/quickstart/#json-response-content

                from ice_rgwa_client import RGWAClient
                # ...
                rgw = RGWAClient(
                    access_key='...',
                    secret_key='...',
                    base_url='...',
                    return_raw_response=True,
                    )
                # ...
                response = rgw.get_user('nonexistent')
                if response.status_code == 404:
                    print("No such user")
                elif response.status_code != 200:
                    print("Problem loading user")
                else:
                    user = response.json()

        """
        if not access_key:
            access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        if not secret_key:
            secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.base_url = base_url
        self.verify = verify
        self.auth = S3Auth(access_key, secret_key, service_url=base_url)
        self.return_raw_response = return_raw_response

    def _request(self, method, endpoint, action=None, data=None, **kwargs):
        """Helper method to factor out actions common to Ceph Rados Gateway
        Admin requests.

        "data" is a dictionary that, if provided, will be JSON-encoded and
        submitted in the body of the request.

        Other keyword arguments will be encoded and used as URL parameters.

        "_" in kwargs will be converted to "-" in URL parameter keys.

        """
        # We can validate some arguments before the round trip to the server
        _validate_args(self.valid_args, **kwargs)

        # We never want to pass literal None to the API, so we can use None to
        # indicate "do not use this k/v pair at all." Using this, optional
        # parameters still appear in the function signature but will be omitted
        # from the request when unspecified.
        params = {
            k.replace('_', '-'): v
            for k, v in kwargs.items()
            if v is not None}

        # Same for body data but without _/- conversion...
        data = {} if data is None else {
            k: v
            for k, v in data.items()
            if v is not None}

        # The Ceph Object Gateway Admin Operations API specifies, for some
        # operations, a key-only URL parameter (that we call "action") with no
        # associated value. For simplicity, we violate the spec slightly by
        # assigning it a value of "". It seems to work.
        if action:
            params[action] = ''

        # JSON output is the default, so there's no need to specify format=json
        # parameter despite all the examples in the docs making it explicit.

        url = '%s/%s' % (self.base_url, endpoint)
        response = request(
            method=method,
            url=url,
            params=params,
            json=data,
            auth=self.auth,
            verify=self.verify,
        )
        if self.return_raw_response:
            return response
        else:
            if response.status_code == 404:
                return None

            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                # At this point we have a successful 200 status but a problem
                # decoding the json. Some responses are empty:
                if not response.content:
                    return {}
                raise

    #
    # These methods appear in the same order as the corresponding endpoints in
    # the documentation. The docstrings are copied verbatim from that
    # documentation. See:
    # http://docs.ceph.com/docs/master/radosgw/adminops/
    #

    def get_usage(self, uid=None, start=None, end=None, show_entries=False,
                  show_summary=False):
        """Request bandwidth usage information.

        Note: this feature is disabled by default, can be enabled by setting
        'rgw enable usage log = true' in the appropriate section of ceph.conf.
        For changes in ceph.conf to take effect, radosgw process restart is
        needed.

        """
        return self._request(
            'get', 'usage',
            uid=uid,
            start=start,
            end=end,
            show_entries=show_entries,
            show_summary=show_summary,
        )

    def trim_usage(self, uid=None, start=None, end=None, remove_all=False):
        """Remove usage information.

        With no dates specified, removes all usage information.

        Note: this feature is disabled by default, can be enabled by setting
        'rgw enable usage log = true' in the appropriate section of ceph.conf.
        For changes in ceph.conf to take effect, radosgw process restart is
        needed.

        """
        return self._request(
            'delete', 'usage',
            uid=uid,
            start=start,
            end=end,
            remove_all=remove_all,
        )

    def get_user(self, uid):
        """Get user information."""
        return self._request('get', 'user', uid=uid)

    def create_user(self, uid, display_name, email=None, key_type='s3',
                    access_key=None, secret_key=None, user_caps=None,
                    generate_key=True, max_buckets=None, suspended=False):
        """Create a new user.

        By default, a S3 key pair will be created automatically and returned in
        the response. If only one of access_key or secret_key is provided, the
        omitted key will be automatically generated. By default, a generated
        key is added to the keyring without replacing an existing key pair. If
        access_key is specified and refers to an existing key owned by the user
        then it will be modified.

        """
        return self._request(
            'put', 'user',
            uid=uid,
            display_name=display_name,
            email=email,
            key_type=key_type,
            access_key=access_key,
            secret_key=secret_key,
            user_caps=user_caps,
            generate_key=generate_key,
            max_buckets=max_buckets,
            suspended=suspended,
        )

    def modify_user(self, uid, display_name=None, email=None, key_type='s3',
                    access_key=None, secret_key=None, user_caps=None,
                    generate_key=True, max_buckets=None, suspended=False):
        """Modify a user."""
        return self._request(
            'post', 'user',
            uid=uid,
            display_name=display_name,
            email=email,
            key_type=key_type,
            access_key=access_key,
            secret_key=secret_key,
            user_caps=user_caps,
            generate_key=generate_key,
            max_buckets=max_buckets,
            suspended=suspended,
        )

    def remove_user(self, uid, purge_data=False):
        """Remove an existing user."""
        return self._request(
            'delete', 'user',
            uid=uid,
            purge_data=purge_data,
        )

    def create_subuser(self, uid, subuser=None,
                       secret_key=None, access_key=None,
                       key_type=None, access=None, generate_secret=False):
        """Create a new subuser.

        (Primarily useful for clients using the Swift API). Note that in
        general for a subuser to be useful, it must be granted permissions by
        specifying access. As with user creation if subuser is specified
        without secret, then a secret key will be automatically generated.

        """
        return self._request(
            'put', 'user', 'subuser',
            uid=uid,
            subuser=subuser,
            secret_key=secret_key,
            access_key=access_key,
            key_type=key_type,
            access=access,
            generate_secret=generate_secret,
        )

    def modify_subuser(self, uid, subuser, secret=None,
                       key_type='swift', access=None, generate_secret=False):
        """Modify an existing subuser."""
        return self._request(
            'post', 'user', 'subuser',
            uid=uid,
            subuser=subuser,
            secret=secret,
            key_type=key_type,
            access=access,
            generate_secret=generate_secret,
        )

    def remove_subuser(self, uid, subuser, purge_keys=True):
        """Remove an existing subuser."""
        return self._request(
            'delete', 'user', 'subuser',
            uid=uid,
            subuser=subuser,
            purge_keys=purge_keys,
        )

    def create_key(self, uid, subuser=None, key_type='s3', access_key=None,
                   secret_key=None, generate_key=True):
        """Create a new key.

        If a subuser is specified then by default created keys will be swift
        type. If only one of access_key or secret_key is provided the committed
        key will be automatically generated, that is if only secret_key is
        specified then access_key will be automatically generated. By default,
        a generated key is added to the keyring without replacing an existing
        key pair. If access_key is specified and refers to an existing key
        owned by the user then it will be modified. The response is a container
        listing all keys of the same type as the key created. Note that when
        creating a swift key, specifying the option access_key will have no
        effect. Additionally, only one swift key may be held by each user or
        subuser.

        """
        return self._request(
            'put', 'user', 'key',
            uid=uid,
            subuser=subuser,
            key_type=key_type,
            access_key=access_key,
            secret_key=secret_key,
            generate_key=generate_key,
        )

    def remove_key(self, access_key, key_type=None, uid=None, subuser=None):
        """Remove an existing key."""
        return self._request(
            'delete', 'user', 'key',
            access_key=access_key,
            key_type=key_type,
            uid=uid,
            subuser=subuser,
        )

    def get_bucket(self, bucket=None, uid=None, stats=False):
        """Get information about a subset of the existing buckets.

        If uid is specified without bucket then all buckets beloning to the
        user will be returned. If bucket alone is specified, information for
        that particular bucket will be retrieved.

        """
        return self._request(
            'get', 'bucket',
            bucket=bucket,
            uid=uid,
            stats=stats,
        )

    def check_bucket_index(self, bucket, check_objects=False, fix=False):
        """Check the index of an existing bucket.

        NOTE: to check multipart object accounting with check-objects, fix must
        be set to True.

        """
        return self._request(
            'get', 'bucket', 'index',
            bucket=bucket,
            check_objects=check_objects,
            fix=fix,
        )

    def remove_bucket(self, bucket, purge_objects=False):
        """Delete an existing bucket."""
        return self._request(
            'delete', 'bucket',
            bucket=bucket,
            purge_objects=purge_objects,
        )

    def unlink_bucket(self, bucket, uid):
        """Unlink a bucket from a specified user.

        Primarily useful for changing bucket ownership.

        """
        return self._request(
            'post', 'bucket',
            bucket=bucket,
            uid=uid,
        )

    def link_bucket(self, bucket, bucket_id, uid):
        """Link a bucket to a specified user, unlinking the bucket from any
        previous user.

        """
        # Both bucket and bucket_id are really required. Use get_bucket() to
        # discover the id of a bucket from its name.
        #
        # FIXME: add a convenience method to look up the id?
        return self._request(
            'put', 'bucket',
            bucket=bucket,
            bucket_id=bucket_id,
            uid=uid,
        )

    def remove_object(self, bucket, object_name):
        """Remove an existing object.

        NOTE: Does not require owner to be non-suspended.

        """
        return self._request(
            'delete', 'bucket', 'object',
            bucket=bucket,
            object_name=object_name,
        )

    def get_policy(self, bucket, object_name=None):
        """Read the policy of an object or bucket."""
        return self._request(
            'get', 'bucket', 'policy',
            bucket=bucket,
            object_name=object_name,
        )

    def add_capability(self, uid, user_caps):
        """Add an administrative capability to a specified user.

        uid (string):
            The user ID to add an administrative capability to.

        user_caps (string):
            The administrative capability to add to the user. Example:
            "usage=read,write;user=write"

        """
        return self._request(
            'put', 'user', 'caps',
            uid=uid,
            user_caps=user_caps,
        )

    def remove_capability(self, uid, user_caps):
        """Remove an administrative capability from a specified user."""
        return self._request(
            'delete', 'user', 'caps',
            uid=uid,
            user_caps=user_caps,
        )

    def get_quota(self, uid, quota_type):
        return self._request(
            'get', 'user', 'quota',
            uid=uid,
            quota_type=quota_type,
        )

    def set_quota(self, uid, quota_type, bucket=None, max_size_kb=None,
                  max_objects=None, enabled=None):
        return self._request(
            'put', 'user', 'quota',
            quota_type=quota_type,
            uid=uid,
            bucket=bucket,
            max_size_kb=max_size_kb,
            max_objects=max_objects,
            enabled=enabled,
        )

    #
    # Convenience methods
    #

    def get_user_quota(self, uid):
        return self.get_quota(uid=uid, quota_type='user')

    def set_user_quota(self, uid, max_size_kb=None,
                       max_objects=None, enabled=None):
        return self.set_quota(
            uid=uid,
            quota_type='user',
            max_size_kb=max_size_kb,
            max_objects=max_objects,
            enabled=enabled,
        )

    def get_user_bucket_quota(self, uid):
        return self.get_quota(uid=uid, quota_type='bucket')

    def set_user_bucket_quota(self, uid, bucket,
                              max_size_kb=None, max_objects=None,
                              enabled=None):
        return self.set_quota(
            uid=uid,
            bucket=bucket,
            quota_type='bucket',
            max_size_kb=max_size_kb,
            max_objects=max_objects,
            enabled=enabled,
        )
