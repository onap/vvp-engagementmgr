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
from rest_framework.status import HTTP_204_NO_CONTENT

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import VF, VFC
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.serializers import VFCModelSerializer
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.vfc_service import VFCSvc


@classDecorator([logFuncEntry])
class VFCRest(VvpApiView):
    vfc_service = VFCSvc()

    @auth(Permissions.get_vfc)
    def get(self, request, vf_uuid):

        vf = VF.objects.get(uuid=vf_uuid)
        vfcs = VFC.objects.filter(vf=vf)
        serializer = VFCModelSerializer(vfcs, many=True)
        return Response(serializer.data)

    """
    expecting: VF object uuid, VFC relevant fields(excluding the ones with default field)
    result: addition of a VFC to the DB and concatenating them with the VF object
    """
    # This method doesn't need to be decorated with auth since it doesn't pass any engagement data from the front-end

    @auth(Permissions.add_vfc)
    def post(self, request):
        data = request.data
        msg = self.vfc_service.create_vfc(data)
        return Response(msg)

    """
    expecting: VFC object uuid
    result: Deletion of the VFC object with vfc_uuid
    """

    @auth(Permissions.delete_vfc)
    def delete(self, request, vf_uuid, vfc_uuid):
        self.vfc_service.delete_vfc(vfc_uuid)
        return Response(status=HTTP_204_NO_CONTENT)
