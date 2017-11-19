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
from rest_framework.status import HTTP_400_BAD_REQUEST,\
    HTTP_500_INTERNAL_SERVER_ERROR

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.checklist_service import CheckListSvc
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.utils.validator import Validator


@classDecorator([logFuncEntry])
class NewCheckList(VvpApiView):

    @auth(Permissions.view_checklist)
    def get(self, request, eng_uuid):

        user = request_data_mgr.get_user()
        eng_uuid = request_data_mgr.get_eng_uuid()
        data = CheckListSvc().getDataForCreateNewChecklist(user, eng_uuid)
        if not data:
            msg = "Create New checklist is not ready yet"
            return Response(msg, status=HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(data)

    @auth(Permissions.is_el_of_eng)
    def post(self, request, eng_uuid):
        data = request.data

        if ('checkListName' not in data or not data['checkListName'] or
            'checkListTemplateUuid' not in data or
            not data['checkListTemplateUuid'] or
                'checkListAssociatedFiles' not in data):
            msg = "One of the CheckList's input parameters is missing"
            self.logger.error(msg)
            return Response(msg, status=HTTP_400_BAD_REQUEST)

        if not Validator.validateCheckListName(data['checkListName']):
            msg = "Invalid characters in check list name."
            self.logger.error(msg)
            return Response(msg, status=HTTP_400_BAD_REQUEST)

        data = CheckListSvc().createOrUpdateChecklist(
            data['checkListName'], data['checkListTemplateUuid'],
            data['checkListAssociatedFiles'], None)

        return Response(data)


@classDecorator([logFuncEntry])
class ExistingCheckList(VvpApiView):

    @auth(Permissions.view_checklist)
    def get(self, request, checklistUuid):
        user = request_data_mgr.get_user()
        checklist_uuid = request_data_mgr.get_cl_uuid()
        data = CheckListSvc().getChecklist(user, checklist_uuid)
        return Response(data)

    @auth(Permissions.is_el_of_eng)
    def delete(self, request):
        CheckListSvc().deleteChecklist(request_data_mgr.get_cl_uuid())
        return Response()

    @auth(Permissions.is_el_of_eng)
    def put(self, request, checklistUuid):
        data = request.data
        if ('checklistUuid' not in data or not data['checklistUuid'] or
            'checkListName' not in data or not data['checkListName'] or
            'checkListTemplateUuid' not in data or
            not data['checkListTemplateUuid'] or
                'checkListAssociatedFiles' not in data):
            msg = "One of the CheckList's input parameters is missing"
            self.logger.error(msg)
            return Response(msg, status=HTTP_400_BAD_REQUEST)
        if not Validator.validateCheckListName(data['checkListName']):
            msg = "Invalid characters in check list name."
            self.logger.error(msg)
            return Response(msg, status=HTTP_400_BAD_REQUEST)

        data = CheckListSvc().createOrUpdateChecklist(
            data['checkListName'], data['checkListTemplateUuid'],
            data['checkListAssociatedFiles'], data['checklistUuid'])

        return Response(data)


@classDecorator([logFuncEntry])
class CheckListTemplates(VvpApiView):

    @auth(Permissions.view_checklist_template)
    def get(self, request, templateUuid=None):
        data = CheckListSvc().getChecklistTemplates(templateUuid)
        return Response(data)

    @auth(Permissions.edit_checklist_template)
    def put(self, request):
        data = request.data
        CheckListSvc().editChecklistTemplate(data)
        return Response()
