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
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import VF, DeploymentTargetSite
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.serializers import \
    ThinDeploymentTargetSiteModelSerializer
from engagementmanager.service.authorization_service import Permissions


@classDecorator([logFuncEntry])
class DTSites(VvpApiView):

    @auth(Permissions.get_deployment_target_site)
    def get(self, request, vf_uuid=None):
        if vf_uuid:
            vf = VF.objects.get(uuid=vf_uuid)
            dtsites = vf.deployment_target_sites
            serializer = ThinDeploymentTargetSiteModelSerializer(
                dtsites, many=True)
            return Response(serializer.data)
        else:
            dtsites = DeploymentTargetSite.objects.all()
            serializer = ThinDeploymentTargetSiteModelSerializer(
                dtsites, many=True)
            return Response(serializer.data)

    """
    expecting: VF object uuid, DeploymentTargetSite uuid
    result: addition of the DeploymentTargetSite object with dtsite_uuid \
    to the VF's deployment_target_sites
    """
    @auth(Permissions.add_deployment_target_site)
    def post(self, request):
        msg = ""
        data = request.data
        name = data['name']
        dtsite = None

        try:
            dtsite = DeploymentTargetSite.objects.get(name=name)
            msg = "DTSite was already existed, hence would next be \
            added to the VF's sites list"
        except DeploymentTargetSite.DoesNotExist:
            dtsite = DeploymentTargetSite.objects.create(name=name)
            dtsite.save()
        vf = VF.objects.get(uuid=data['vf_uuid'])
        vf.deployment_target_sites.add(dtsite)
        vf.save()
        return Response(msg)

    @auth(Permissions.delete_deployment_target_site)
    def delete(self, request, vf_uuid, dts_uuid):
        msg = "OK"
        dtsite = None
        vf = None

        if vf_uuid and dts_uuid:
            dtsite = DeploymentTargetSite.objects.get(uuid=dts_uuid)
            vf = VF.objects.get(uuid=vf_uuid)
            vf.deployment_target_sites.remove(dtsite)
            vf.save()
            return Response(msg, status=HTTP_204_NO_CONTENT)
        else:
            msg = "dtsite uuid or vf uuid, wasn't provided"
            self.logger.error(msg)
            return Response(msg, status=HTTP_400_BAD_REQUEST)
