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
from rest_framework import status
from rest_framework.response import Response

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.slack_client.api import SlackClient
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.models import Feedback as FeedbackModal


@classDecorator([logFuncEntry])
class Feedback(VvpApiView):

    slack_client = SlackClient()

    @auth(Permissions.add_feedback)
    def post(self, request):
        user = request_data_mgr.get_user()
        if ('description' not in request.data or not request.data['description']):
            raise KeyError("One of the input parameters are missing")
        new_description = request.data['description']
        new_feedback = FeedbackModal(
            user=user,
            description=new_description
        )
        new_feedback.save()
        self.slack_client.send_slack_notifications_for_new_feedback(new_feedback, user)

        return Response(status.HTTP_200_OK)
