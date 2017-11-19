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
from django.conf import settings
from rest_framework.response import Response

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import Engagement
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.serializers import ActivityModelSerializer
from engagementmanager.service.activities_service import ActivitiesSvc
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.utils.request_data_mgr import request_data_mgr


@classDecorator([logFuncEntry])
class PullActivities(VvpApiView):
    def __init__(self):
        self.activities_service = ActivitiesSvc()

    @auth(Permissions.pull_activities)
    def get(self, request, eng_uuid, num=None):
        if not num:
            num = settings.NUMBER_OF_POLLED_ACTIVITIES
        eng = Engagement.objects.get(uuid=request_data_mgr.get_eng_uuid())
        activities = self.activities_service.pull_recent_activities(
            eng, recent_activities_limit=num)
        serializer = ActivityModelSerializer(activities, many=True)
        return Response(serializer.data)
