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
from django.apps import AppConfig
from django.conf import settings
from engagementmanager.scheduled_jobs import ScheduledJobs
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()

cms_client = None
bus_service = None


class EngagementmanagerConfig(AppConfig):
    name = 'engagementmanager'
    verbose_name = "engagementmanager"

    def ready(self):
        # This otherwise unused import causes the signal receivers
        # to register themselves at the appropriate time. Do not remove.
        # We use logger.debug to ignore flake8's warning about unused import.
        import engagementmanager.vm_integration.em_api
        logger.debug(engagementmanager.vm_integration.em_api.file_name)
        ###############################
        # Bootstrap Actions           #
        ###############################
        from engagementmanager.utils.constants import Constants

        if (settings.DOMAIN == Constants.prodDomain):
            logger.info("--Production Mode--")
        else:
            logger.info("--Development Mode--")

        from engagementmanager.cms_client.api import CMSClient
        global cms_client
        cms_client = CMSClient()
        global bus_service
        from engagementmanager.service.bus_service import BusService
        bus_service = BusService()
        self.__register_bus_service_handlers()

        ice_scheduler = ScheduledJobs(bus_service)
        ice_scheduler.setup_daily_job()
        ice_scheduler.setup_hourly_job()

    def __register_bus_service_handlers(self):
        from engagementmanager.bus.messages.activity_event_message import \
            ActivityEventMessage
        from engagementmanager.bus.messages.daily_scheduled_message import \
            DailyScheduledMessage
        from engagementmanager.bus.messages.new_notification_message import \
            NewNotificationMessage
        from engagementmanager.bus.handlers.activity_event_handler import\
            ActivityEventHandler
        from engagementmanager.bus.handlers.daily_resend_notifications_handler\
            import DailyResendNotificationsHandler
        from engagementmanager.bus.handlers.digest_email_notification_handler\
            import DigestEmailNotificationHandler
        from engagementmanager.bus.handlers.new_notification_handler\
            import NewNotificationHandler
        from engagementmanager.bus.messages.hourly_scheduled_message\
            import HourlyScheduledMessage
        from engagementmanager.bus.handlers.\
            check_news_and_announcements_handler import \
            CheckNewsAndAnnouncementsHandler
        from engagementmanager.bus.handlers.\
            daily_notify_inactive_engagements_handler import \
            DailyNotifyInactiveEngagementsHandler
        from engagementmanager.bus.handlers.image_pushed_handler import \
            ImagePushedHandler

        bus_service.register(ActivityEventHandler(), ActivityEventMessage)
        bus_service.register(NewNotificationHandler(), NewNotificationMessage)
        bus_service.register(
            DigestEmailNotificationHandler(), DailyScheduledMessage)
        bus_service.register(
            DailyResendNotificationsHandler(), DailyScheduledMessage)
        bus_service.register(
            DailyNotifyInactiveEngagementsHandler(), DailyScheduledMessage)
        bus_service.register(
            CheckNewsAndAnnouncementsHandler(), HourlyScheduledMessage)
        bus_service.register(ImagePushedHandler(), HourlyScheduledMessage)