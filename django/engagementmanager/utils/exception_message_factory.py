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
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import CommandError
from engagementmanager.utils.vvp_exceptions import VvpObjectNotAvailable, \
    VvpGeneralException, VvpBadRequest, VvpConflict
from itsdangerous import SignatureExpired
from requests import ConnectionError
from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed, NotAuthenticated, \
    PermissionDenied, NotAcceptable


class ExceptionMessageFactory:
    messages_dictionary = {
        ObjectDoesNotExist.__name__: {
            'msg': 'User or Password does not match',
            'include_exception': False,
            'status': status.HTTP_404_NOT_FOUND},
        MethodNotAllowed.__name__: {
            'msg': 'Method not allowed: ',
            'include_exception': True,
            'status':
            status.HTTP_405_METHOD_NOT_ALLOWED},
        NotAuthenticated.__name__: {
            'msg': 'You must authenticate in order to perform this action: ',
            'include_exception': True, 'status': status.HTTP_403_FORBIDDEN},
        SignatureExpired.__name__: {
            'msg': 'Signature expired for this token: ',
            'include_exception': True,
            'status':
            status.HTTP_405_METHOD_NOT_ALLOWED},
        KeyError.__name__: {
            'msg': 'KeyError occurred over the backend.',
            'include_exception': True,
            'include_additional_exc_str': True, 'status':
            status.HTTP_400_BAD_REQUEST},
        ValueError.__name__: {
            'msg': 'ValueError occurred over the backend: ',
            'include_exception': True,
            'status': status.HTTP_500_INTERNAL_SERVER_ERROR},
        ConnectionError.__name__: {
            'msg': 'ConnectionError occurred over the backend: ',
            'include_exception': True,
            'status': status.HTTP_500_INTERNAL_SERVER_ERROR},
        ImportError.__name__: {
            'msg': 'ImportError occurred over the backend: ',
            'include_exception': True,
            'status': status.HTTP_500_INTERNAL_SERVER_ERROR},
        CommandError.__name__: {
            'msg': 'CommandError occurred over the backend: ',
            'include_exception': True,
            'status': status.HTTP_500_INTERNAL_SERVER_ERROR},
        PermissionDenied.__name__: {
            'msg': 'PermissionDenied occurred over the backend: ',
            'include_exception': True,
            'status': status.HTTP_401_UNAUTHORIZED},
        VvpObjectNotAvailable.__name__: {
            'msg': '', 'include_exception': True,
            'status': status.HTTP_410_GONE},
        NotAcceptable.__name__: {
            'msg': '', 'include_exception': True,
            'status': status.HTTP_403_FORBIDDEN},
        VvpGeneralException.__name__: {
            'msg': '', 'include_exception': True,
            'status': status.HTTP_500_INTERNAL_SERVER_ERROR},
        FileExistsError.__name__: {
            'msg': 'Not modified due to: ', 'include_exception': True,
            'status': status.HTTP_304_NOT_MODIFIED},
        VvpBadRequest.__name__: {
            'msg': '', 'include_exception': True,
            'status': status.HTTP_400_BAD_REQUEST},
        VvpConflict.__name__: {
            'msg': '', 'include_exception': True,
            'status': status.HTTP_409_CONFLICT},
        Exception.__name__: {
            'msg': 'General error on backend: ',
            'include_exception': True,
            'status': status.HTTP_500_INTERNAL_SERVER_ERROR},
    }

    def get_exception_message(self, exception):
        if isinstance(exception, ObjectDoesNotExist):
            result = self.messages_dictionary[ObjectDoesNotExist.__name__]
        elif exception.__class__.__name__ in self.messages_dictionary:
            result = self.messages_dictionary[exception.__class__.__name__]
        else:
            result = self.messages_dictionary[Exception.__name__]

        return result
