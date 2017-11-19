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
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT

from engagementmanager.bus.messages.activity_event_message import \
    ActivityEventMessage
from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import NextStep
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.utils.activities_data import DeleteNextStepsActivityData
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.nextstep_service import NextStepSvc
from engagementmanager.utils.constants import NextStepState
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.apps import bus_service


@classDecorator([logFuncEntry])
class UserNextSteps(VvpApiView):

    def get(self, request):
        data_or_msg, count = NextStepSvc().get_user_next_steps(
            5, NextStepState.Incomplete.name)  # @UndefinedVariable
        return Response({'data': data_or_msg.data, 'count': count})


@classDecorator([logFuncEntry])
class NextSteps(VvpApiView):

    @auth(Permissions.set_nextstep)
    def post(self, request, **kwargs):
        dataList = request.data
        eng_uuid = request_data_mgr.get_eng_uuid()
        user = request_data_mgr.get_user()

        for data in dataList:
            if ('description' not in data or not data['description']):
                msg = "One of the input parameters is missing"
                self.logger.error(msg)
                return Response(msg, status=HTTP_400_BAD_REQUEST)

        data = NextStepSvc().addNextStep(dataList)

        for next_step in data:
            if next_step['files']:
                next_step['files'] = json.loads(next_step['files'])

        self.logger.debug(
            "Successfully added a Next Step to engagement_uuid=" +
            eng_uuid +
            " for creator with uuid=" +
            str(user))
        return Response(data)

    @auth(Permissions.eng_membership)
    def get(self, request, **kwargs):
        next_steps_data = NextStepSvc().get_next_steps(
            eng_stage=kwargs['eng_stage'])
        return Response(next_steps_data.data)

    @auth(Permissions.update_personal_next_step)
    def put(self, request, **kwargs):
        data = request.data
        ns_state = attribute = None
        if ('attr' in kwargs):
            attribute = kwargs['attr']
        if ('state' in data):
            ns_state = data['state']
        NextStepSvc().set_next_step_status(attr=attribute, state=ns_state)
        return Response()


@classDecorator([logFuncEntry])
class OrderNextSteps(VvpApiView):

    @auth(Permissions.order_nextstep)
    def put(self, request, eng_uuid):
        data = request.data
        NextStepSvc().update_next_steps_order(nextsteps=data)
        return Response()


@classDecorator([logFuncEntry])
class EditNextSteps(VvpApiView):
    @auth(Permissions.edit_nextstep)
    def put(self, request, ns_uuid):
        data = request.data
        NextStepSvc().update_next_step(data)
        return Response()

    @auth(Permissions.delete_nextstep)
    def delete(self, request, ns_uuid):
        ns = self.get_entity(NextStep, request_data_mgr.get_ns_uuid())
        ns.delete()

        activity_data = DeleteNextStepsActivityData(
            request_data_mgr.get_user(), ns.engagement)
        bus_service.send_message(ActivityEventMessage(activity_data))

        return Response(status=HTTP_204_NO_CONTENT)


@classDecorator([logFuncEntry])
class ChecklistNextStep(VvpApiView):

    @auth(Permissions.add_checklist_nextstep)
    def post(self, request, eng_uuid, checklistUuid):
        body_unicode = request.body
        dataList = json.loads(body_unicode)
        msg = "OK"

        if (not request_data_mgr.get_cl_uuid() or not
                request_data_mgr.get_eng_uuid()):
            msg = "check list uuid or engagement uuid is missing from the " +\
                "url path parameters"
            self.logger.error(msg)
            return Response(msg, status=HTTP_400_BAD_REQUEST)

        for data in dataList:
            if ('assigneesUuids' not in data or not data['assigneesUuids'] or
                'description' not in data or not data['description'] or
                    'duedate' not in data or not data['duedate']):
                msg = "One of the CheckList's input parameters is missing"
                self.logger.error(msg)
                return Response(msg, status=HTTP_400_BAD_REQUEST)

        data = NextStepSvc().addNextStep(
            dataList, desc="Checklist is denied due to a creation " +
            "of a new NextStep")

        return Response(data)
