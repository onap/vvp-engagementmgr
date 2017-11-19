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

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.serializers import SuperThinChecklistModelSerializer
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.checklist_state_service import set_state
from engagementmanager.utils.request_data_mgr import request_data_mgr


@classDecorator([logFuncEntry])
class ChecklistState(VvpApiView):

    @auth(Permissions.update_checklist_state)
    def put(self, request, checklistUuid):
        data = request.data
        decline = data['decline']
        if decline == "True":
            checklist = set_state(True, request_data_mgr.get_cl_uuid(),
                                  isMoveToAutomation=False,
                                  description=data['description'])
        else:
            checklist = set_state(
                False, request_data_mgr.get_cl_uuid(),
                description=data['description'])

        cldata = json.dumps(SuperThinChecklistModelSerializer(
            checklist).data, ensure_ascii=False)
        return Response(cldata)
