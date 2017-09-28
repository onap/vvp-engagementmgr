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
from django.template.loader import get_template
from engagementmanager import mail
from engagementmanager.bus.handlers.service_bus_base_handler import ServiceBusBaseHandler
from engagementmanager.mail import sendMail
from engagementmanager.models import Notification
from engagementmanager.utils.constants import Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class DailyResendNotificationsHandler(ServiceBusBaseHandler):
    def handle_message(self, bus_message):
        logger.debug("New resend notifications message arrived - emails is about to sent to the "
                     "all unsent notifications")
        unsent_notifications = Notification.objects.filter(is_sent=False)
        for notification in unsent_notifications:
            if notification.user.email_updates_on_every_notification:
                try:
                    subject_template = get_template("{notification_template_dir}notification_mail_subject.html".format(
                        notification_template_dir=Constants.notification_template_dir))
                    msg_template = get_template("{notification_template_dir}notification_mail_body.html".format(
                        notification_template_dir=Constants.notification_template_dir))

                    sendMail(notification.user.email, json.loads(notification.activity.metadata),
                             msg_template, subject_template, mail_from=mail.ice_admin_mail_from)
                    notification.is_sent = True
                    notification.save()
                except Exception as e:
                    msg = "Something went wrong while trying to resend bulk mail " \
                          "as part of the notifications daily resend"
                    logger.error(msg + " " + e)
            else:
                notification.is_sent = True
                notification.save()
                logger.info("User choose not to get email on every notification, set it as sent.")
