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
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from engagementmanager.bus.messages.daily_scheduled_message\
    import DailyScheduledMessage
from engagementmanager.bus.messages.hourly_scheduled_message\
    import HourlyScheduledMessage
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class ScheduledJobs:
    def __init__(self, bus_service):
        self.bus_service = bus_service
        self.background_scheduler = BackgroundScheduler()
        self.background_scheduler.start()

    def __daily_scheduled_job(self):
        logger.debug("Daily scheduled job is about to start.")
        self.bus_service.send_message(DailyScheduledMessage())

    def setup_daily_job(self):
        self.background_scheduler.add_job(self.__daily_scheduled_job, 'cron',
                                          hour=settings.
                                          DAILY_SCHEDULED_JOB_HOUR, day='*')

    def __hourly_scheduled_job(self):
        logger.debug("Hourly scheduled job is about to start.")
        self.bus_service.send_message(HourlyScheduledMessage())

    def setup_hourly_job(self):
        self.background_scheduler.add_job(
            self.__hourly_scheduled_job, 'cron', minute=0, hour='*', day='*')
