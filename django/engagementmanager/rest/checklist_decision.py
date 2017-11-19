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

from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.checklist_decision_service import setDecision, \
    getDecision
from engagementmanager.utils.request_data_mgr import request_data_mgr


@classDecorator([logFuncEntry])
class ClDecision(VvpApiView):

    @auth(Permissions.view_checklist)
    def get(self, request, decision_uuid):
        user = request_data_mgr.get_user()
        decisionUuid = decision_uuid
        data = getDecision(decisionUuid, user)
        return Response(data)

    @auth(Permissions.update_checklist_decision)
    def put(self, request, decision_uuid):
        data = request.data

        user = request_data_mgr.get_user()
        decisionUuid = decision_uuid
        if 'value' not in data or not data['value']:
            msg = "value for decision is not provided in the request's body"
            self.logger.error(msg)
            return Response(msg, status=HTTP_400_BAD_REQUEST)
        value = data['value']
        msg = setDecision(decisionUuid, user, value)
        msg = json.dumps(msg, ensure_ascii=False)
        return Response(msg)
