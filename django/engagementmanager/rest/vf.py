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
from rest_framework.status import HTTP_400_BAD_REQUEST

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.vf_service import VFSvc
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.utils.validator import logEncoding
from engagementmanager.views_helper import createVF


@classDecorator([logFuncEntry])
class VF(VvpApiView):

    vf_svc = VFSvc()

    @auth(Permissions.add_vf)
    def post(self, request):
        user = request_data_mgr.get_user()
        vfList = []
        if user is not None:
            vfList = createVF(user, request)
            return Response(vfList)
        else:
            msg = "User wasn't found on top of the kwargs"
            sts = HTTP_400_BAD_REQUEST
            self.logger.error(logEncoding(msg))
            msg = "Action Failed"
            return Response(msg, status=sts)

    def get(self, request, vf_uuid):
        vf_version = self.vf_svc.get_vf_version(vf_uuid)
        return Response(vf_version)
