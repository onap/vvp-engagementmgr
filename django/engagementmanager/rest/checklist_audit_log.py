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

from rest_framework.response import Response

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import ChecklistDecision, Checklist
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.checklist_audit_log_service \
    import getAuditLogsWithChecklist, addAuditLogToChecklist, \
    getAuditLogsWithDecision, addAuditLogToDecision
from engagementmanager.utils.request_data_mgr import request_data_mgr


@classDecorator([logFuncEntry])
class ChecklistAuditLog(VvpApiView):

    @auth(Permissions.view_checklist)
    def get(self, request, checklistUuid):
        user = request_data_mgr.get_user()
        checklistUuid = request_data_mgr.get_cl_uuid()()
        data = getAuditLogsWithChecklist(checklistUuid, user)
        return Response(data)

    @auth(Permissions.create_checklist_audit_log)
    def post(self, request, checklistUuid):
        data = request.data
        user = request_data_mgr.get_user()
        checklistUuid = request_data_mgr.get_cl_uuid()

        if ('description' not in data or not data['description']):
            msg = "description for the audit log is " +\
                "not provided in the request's body"
            self.logger.error(msg)
            raise KeyError(msg)
        description = data['description']
        checklist = Checklist.objects.get(uuid=checklistUuid)
        data = addAuditLogToChecklist(checklist, description, user)
        return Response(data)


@classDecorator([logFuncEntry])
class DecisionAuditLog(VvpApiView):

    @auth(Permissions.view_checklist)
    def get(self, request, decision_uuid):
        user = request_data_mgr.get_user()
        decisionUuid = decision_uuid
        data = getAuditLogsWithDecision(decisionUuid, user)

        return Response(data)

    @auth(Permissions.create_checklist_decision)
    def post(self, request, decision_uuid):
        data = request.data
        user = request_data_mgr.get_user()
        decisionUuid = decision_uuid
        if ('description' not in data or not data['description']):
            msg = "value for decision is not provided in the request's body"
            self.logger.error(msg)
            raise KeyError(msg)
        description = data['description']
        decision = ChecklistDecision.objects.get(uuid=decisionUuid)
        auditData = addAuditLogToDecision(decision, description, user)
        return Response(auditData)
