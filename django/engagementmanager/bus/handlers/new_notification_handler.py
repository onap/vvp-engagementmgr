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
from engagementmanager import mail
from engagementmanager.bus.handlers.service_bus_base_handler import \
    ServiceBusBaseHandler
from django.template.loader import get_template
from engagementmanager.mail import sendMail
from engagementmanager.utils.constants import Constants
from engagementmanager.service.logging_service import LoggingServiceFactory


logger = LoggingServiceFactory.get_logger()


class NewNotificationHandler(ServiceBusBaseHandler):

    def handle_message(self, bus_message):
        logger.info(
            "New notification " +
            "(%s) arrived - email will sent" % bus_message.notification.uuid)

        user = bus_message.notification.user
        if user.email_updates_on_every_notification:
            try:
                template_dir = Constants.notification_template_dir
                subject_template = get_template(
                    """{template_dir}notification_mail_subject.html""".format(
                        template_dir=template_dir))
                msg_template = get_template(
                    """{template_dir}notification_mail_body.html""".format(
                        template_dir=template_dir))
                sendMail(
                    user.email,
                    json.loads(
                        bus_message.notification.activity.metadata),
                    msg_template,
                    subject_template,
                    mail_from=mail.ice_admin_mail_from)
                bus_message.notification.is_sent = True
                bus_message.notification.save()
            except Exception as e:
                msg = "Something went wrong while trying to send " +\
                    "bulk mail as part of the notification"
                logger.error(msg + " " + str(e))
        else:
            bus_message.notification.is_sent = True
            bus_message.notification.save()
            logger.info(
                "User choose not to get email on every " +
                "notification, set it as sent.")
