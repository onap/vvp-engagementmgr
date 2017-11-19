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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import ECOMPRelease
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.serializers import ECOMPReleaseModelSerializer
from engagementmanager.service.ecomp_service import update_ECOMP


@classDecorator([logFuncEntry])
class ECOMPReleaseRESTMethods(VvpApiView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, engagement_uuid, ecomp_uuid):
        msg = "OK"
        if engagement_uuid and ecomp_uuid:
            update_ECOMP(engagement_uuid, ecomp_uuid)
            return Response(msg)
        else:
            msg = "ECOMPRelease PUT Request failed, engagement_uuid wasn't \
            found in kwargs or its content is empty, therefore cannot filter \
            by it to find the required VF"
            self.logger.error(msg)
            msg = "Action failed."
            return Response(msg, status=HTTP_400_BAD_REQUEST)

    def get(self, request):
        ecomp_releases = ECOMPRelease.objects.filter(
            ui_visibility=True).order_by('weight')
        serializer = ECOMPReleaseModelSerializer(ecomp_releases, many=True)
        return Response(serializer.data)
