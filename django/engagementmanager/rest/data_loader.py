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
from uuid import uuid4

from django.utils import timezone
from rest_framework.response import Response

from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import IceUserProfile, Vendor, Role, CustomUser
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.utils.constants import Constants
from engagementmanager.utils.validator import logEncoding
from engagementmanager.views_helper import createUserTemplate


@classDecorator([logFuncEntry])
class EngLeadsDataLoader(VvpApiView):

    def get(self, request):
        data = request.data
        service_provider_company = Vendor.objects.get(name=Constants.service_provider_company_name)
        el_role = Role.objects.get(name="el")
        for el in data:
            user_object = CustomUser.objects.create_user(
                username=el['full_name'], email=el['full_name'], password=el['password'], is_active=False, activation_token=uuid4(), activation_token_create_time=timezone.now())
            data = createUserTemplate(service_provider_company, el['full_name'], el_role, '', True, None, True, user_object)
            el_user, is_profile_created = IceUserProfile.objects.update_or_create(
                email=user_object.email, defaults=data)
            self.logger.info("User: " + el_user.full_name +
                             " was created successfully during bulk_load_engagement_leads function")
        self.logger.info("All users were created successfully during bulk_load_engagement_leads function")
        return Response()


@classDecorator([logFuncEntry])
class CompaniesDataLoader(VvpApiView):

    def get(self, request):
        data = request.data
        for vendor in data:
            Vendor.objects.get_or_create(name=vendor['name'], defaults={'public': True})
            self.logger.info('Company found or created during bulk load vendors: ' + logEncoding(vendor))
        self.logger.info("All companies were created successfully during bulk_load_companies function")
        return Response()
