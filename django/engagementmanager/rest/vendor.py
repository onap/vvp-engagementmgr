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
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import HTTP_409_CONFLICT, HTTP_204_NO_CONTENT

from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import Vendor
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.serializers import ThinVendorModelSerializer


@classDecorator([logFuncEntry])
class VendorREST(VvpApiView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request):
        self.permission_classes = (AllowAny,)
        vendors = Vendor.objects.filter(public=True)
        serializer = ThinVendorModelSerializer(vendors, many=True)
        return Response(serializer.data)

    """
    expecting: Vendor object fields
    result: addition of a Vendor object to the DB
    """

    def post(self, request):
        msg = ""
        sts = None
        data = request.data

        vendor = None
        try:
            vendor = Vendor.objects.get(name=data['name'])
            msg = "Company: " + vendor.name + " already exist"
            self.logger.error(msg)
            sts = HTTP_409_CONFLICT
            return Response(msg, status=sts)
        # If the VFC Does not exist, then continue as usual and create it.
        except Vendor.DoesNotExist:
            company = Vendor.objects.create(name=data['name'], public=False)
            company.save()
        return Response(msg)

    """
    expecting: Vendor object uuid
    result: Deletion of the Vendor object from the DB
    """

    def delete(self, request, uuid):
        msg = ""
        sts = HTTP_204_NO_CONTENT
        Vendor.objects.get(uuid=uuid).delete()
        return Response(msg, status=sts)
