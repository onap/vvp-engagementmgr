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
from django.db.models.query_utils import Q
from django.utils import timezone
from django.utils.timezone import timedelta
from engagementmanager.bus.handlers.service_bus_base_handler import ServiceBusBaseHandler
from engagementmanager.models import Engagement, VF
from engagementmanager.service.activities_service import ActivitiesSvc
from engagementmanager.service.checklist_service import CheckListSvc
from engagementmanager.service.engagement_service import archive_engagement
from engagementmanager.utils.constants import EngagementStage
from engagementmanager.utils.activities_data import NoticeEmptyEngagementData
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class DailyNotifyInactiveEngagements(ServiceBusBaseHandler):
    def handle_message(self, bus_message):
        logger.debug("New digest bus message arrived - email is about to sent")
        checklist_service = CheckListSvc()
        engagements_list = Engagement.objects.filter(is_with_files=False, Q(engagement_stage=EngagementStage.Active.name) | Q(engagement_stage=EngagementStage.Intake.name))

        for engagement in engagements_list:
            files_found = checklist_service.getEngagementFiles(engagement.uuid)
            if files_found:
                engagement.is_with_files = True
                engagement.save()
                continue

            max_empty_time = self.get_max_empty_date(engagement.create_time)

            if max_empty_time < timezone.now():
                archive_engagement(engagement.uuid, "More than 30 days passed and no files added to gitlab yet")
            else:
                self.send_emails_logic(engagement)

    @staticmethod
    def get_max_empty_date(creation_time):
        return creation_time + timedelta(days=30)

    @staticmethod
    def get_days_delta(start_time, end_time):
        return (end_time - start_time).days

    def send_emails_logic(self, engagement):

        delta_days_from_creation = self.get_days_delta(engagement.create_time, timezone.now())
        alert_days = [7, 14, 21]
        if (delta_days_from_creation in alert_days) or (delta_days_from_creation >= 23 and delta_days_from_creation < 30):
            vf = VF.objects.get(engagement=engagement)
            vf_name = vf.name
            max_empty_time = self.get_max_empty_date(engagement.create_time).strftime('%b %d, %Y')
            git_repo_url = vf.git_repo_url
            activity_data = NoticeEmptyEngagementData(
                vf_name, max_empty_time, git_repo_url, str(delta_days_from_creation), engagement)
            ActivitiesSvc().generate_activity(activity_data)
