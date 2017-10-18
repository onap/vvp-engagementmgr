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
from django.conf import settings
from django.core.mail import send_mail, send_mass_mail

from engagementmanager.service.logging_service import LoggingServiceFactory
from engagementmanager.utils.constants import TemplatesConstants

ice_admin_mail_from = settings.CONTACT_FROM_ADDRESS

logger = LoggingServiceFactory.get_logger()


def sendMail(email, data, mail_body_template, mail_subject_template, mail_from=ice_admin_mail_from):
    logger.debug("about to send mail to " + email)
    if data is None:
        data = {}
    data.update(TemplatesConstants.context)
    html_msg = mail_body_template.render(context=data)
    mail_subject = mail_subject_template.render(context=data)
    # send mail with template
    send_mail(mail_subject, '', "D2 ICE Team <" + mail_from + ">", [email], fail_silently=False, html_message=html_msg)
    logger.debug("Looks like email delivery to " + email + " has succeeded")


def sendBulkMail(datatuple):
    logger.debug("about to send mail")

    try:
        num_sent = send_mass_mail(datatuple)
        logger.debug("Looks like email delivery has succeeded. Number of sent mails is " + str(num_sent))
        return num_sent
    except Exception as e:  # Dont remove try-except since it is invoked from Notification Bot
        logger.error("Email delivery has failed. Error is: " + str(e))
        raise e
