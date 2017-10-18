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

from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.service.cms.pages_service import CMSPagesService


@classDecorator([logFuncEntry])
class Pages(VvpApiView):
    cms_service = CMSPagesService()

    def get(self, request, format=None, **kwargs):
        titleParam = request.GET.get('title', "")

        pages = self.cms_service.getPages(titleParam)
        return Response(pages)


@classDecorator([logFuncEntry])
class PageById(VvpApiView):
    cms_service = CMSPagesService()

    def get(self, request, format=None, **kwargs):
        idParam = kwargs['id']

        pages = self.cms_service.getPage(idParam)
        return Response(pages)


@classDecorator([logFuncEntry])
class PageSearch(VvpApiView):
    cms_service = CMSPagesService()

    def get(self, request):
        keyword = request.GET.get('keyword', "")
        result = []

        if keyword is not None and keyword != "":
            result = self.cms_service.searchPages(keyword)

        return Response(result)
