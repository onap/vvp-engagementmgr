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
""" populate_all_gitlab_repo_and_user_and_jenkins
Will populate gitlab and jenkins with vf data (where it's not exists).

This command will be used for systems
with missing gitlab/jenkins data for some vfs.
"""
from django.core.management.base import BaseCommand
from rest_framework.status import HTTP_200_OK
from engagementmanager.models import VF
from engagementmanager.utils.constants import EngagementStage
from engagementmanager.utils.validator import logEncoding
from engagementmanager.vm_integration import vm_client
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class Command(BaseCommand):

    def handle(self, *args, **options):
        engStageList = [EngagementStage.Intake.name,
                        EngagementStage.Active.name,
                        EngagementStage.Validated.name,
                        EngagementStage.Completed.name]
        vf_list = VF.objects.filter(
            engagement__engagement_stage__in=engStageList)
        log_array = []
        error_array = []
        for vf_found in vf_list:
            logger.debug(vf_found.uuid)
            msg, http_status, values = vm_client.send_provision_new_vf_event(
                vf_found)
            vf_dict = {
                'vf_uuid': vf_found.uuid,
                'msg': msg,
                'http_status': http_status,
                'values': values
            }

            log_array.append(vf_dict)
            if (http_status != HTTP_200_OK):
                error_array.append(vf_dict)

        logger.error("==== populate jenkins _ gitlab error log ======")
        logger.error(logEncoding(error_array))
