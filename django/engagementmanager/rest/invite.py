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
import json

from rest_framework import status
from rest_framework.response import Response

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.invite_service import inviteUserToSignUpOrLogin
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.utils.validator import logEncoding


@classDecorator([logFuncEntry])
class InviteTeamMember(VvpApiView):

    @auth(Permissions.invite)
    def post(self, request):
        inviterUser = request_data_mgr.get_user()
        msg = "OK"
        sts = status.HTTP_200_OK
        if (inviterUser != None):
            dataList = []
            dataList = request.data

            for data in dataList:
                if 'eng_uuid' in data and data['eng_uuid'] and 'email' in data and data['email']:
                    inviteUserToSignUpOrLogin(inviterUser, data, is_contact_user=False)
                else:
                    msg = "No eng_uuid or no email found on the request body to invite-team-members. data=" + str(data)
                    self.logger.error(logEncoding(msg))
                    sts = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(msg, status=sts)


@classDecorator([logFuncEntry])
class InviteContact(VvpApiView):

    @auth(Permissions.invite)
    def post(self, request):
        msg = "OK"
        sts = status.HTTP_200_OK
        data = request.data

        if ('full_name' not in data or not data['full_name'] or
           'email' not in data or not data['email'] or
           'phone_number' not in data or not data['phone_number'] or
           'eng_uuid' not in data or not data['eng_uuid']):
            msg = "One of the input parameters is missing"
            self.logger.error(msg)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        inviterUser = request_data_mgr.get_user()
        inviteUserToSignUpOrLogin(inviterUser, data, is_contact_user=True)

        return Response(msg, status=sts)
