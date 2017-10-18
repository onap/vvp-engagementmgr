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
""" render_rgwa_credentials
Will create rados gateway user (S3 API) for each django user.

This command will create the user if it's not exists so it safe to run it even the user are exists.
This command is part of bucket usage (images) efforts.
"""
from django.db.models import Q
from engagementmanager.models import IceUserProfile
from validationmanager.em_integration.vm_api import create_user_rgwa
from django.core.management.base import BaseCommand
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.debug("About to generate RGWA credentials for existing users")
        users = IceUserProfile.objects.filter(
            Q(rgwa_secret_key=None) | Q(rgwa_access_key=None))
        for user in users:
            create_user_rgwa(user)
