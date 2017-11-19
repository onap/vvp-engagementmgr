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
import mock
from rest_framework.status import HTTP_202_ACCEPTED
from engagementmanager.bus.messages.activity_event_message import \
    ActivityEventMessage
from engagementmanager.bus.messages.daily_scheduled_message import \
    DailyScheduledMessage
from engagementmanager.models import Vendor
from engagementmanager.utils.activities_data import \
    UserJoinedEngagementActivityData
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants, EngagementStage
from engagementmanager.apps import bus_service
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def digest_mock(self, bus_message):
    DigestEmailNotificationsTestCase.is_digested_mock_sent = True
    DigestEmailNotificationsTestCase.message = bus_message


# engagementmanager/bus/handlers/digest_email_notification_handler.py
@mock.patch('engagementmanager.bus.handlers.digest_email_notification_handler.'
            'DigestEmailNotificationHandler.handle_message', digest_mock)
class DigestEmailNotificationsTestCase(TestBaseEntity):
    is_digested_mock_sent = False
    message = None

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])

        self.createDefaultRoles()
        vendor = Vendor.objects.get(
            name=Constants.service_provider_company_name)
        self.el_user = self.creator.createUser(
            vendor,
            self.randomGenerator("main-vendor-email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.el,
            True)
        vendor = Vendor.objects.get(name='Other')
        self.user = self.creator.createUser(
            vendor,
            self.randomGenerator("email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.standard_user,
            True)
        self.pruser = self.creator.createUser(
            vendor,
            self.randomGenerator("email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.standard_user,
            True)

        self.engagement = self.creator.createEngagement(self.randomGenerator(
            "randomString"), self.randomGenerator("randomString"), None)
        self.engagement.engagement_team.add(self.user, self.el_user)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.pruser
        self.engagement.save()

        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"),
            self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(
            self.randomGenerator("randomString"),
            self.engagement,
            self.deploymentTarget,
            False,
            vendor)

    def testDigestEmailForActivities(self):
        """
        Will check if the service bus deliver the
        message of sending digested mails
        No need to check if the mail is sent or if the
        python scheduling is working
        """
        # Create the activities:
        self.urlStr = self.urlPrefix + "single-engagement/" + \
            str(self.engagement.uuid) + "/stage/@stage"

        random_user = self.creator.createUser(Vendor.objects.get(name='Other'),
                                              self.randomGenerator("email"),
                                              self.randomGenerator(
                                                  "randomNumber"),
                                              self.randomGenerator(
                                                  "randomString"),
                                              self.el, True)

        self.engagement.engagement_team.add(random_user)
        self.engagement.save()

        users_list = []
        users_list.append(random_user)
        activity_data = UserJoinedEngagementActivityData(
            self.vf, users_list, self.engagement)
        bus_service.send_message(ActivityEventMessage(activity_data))

        token = self.loginAndCreateSessionToken(random_user)
        response = self.c.put(self.urlStr.replace("@stage",
                                                  EngagementStage.Active.name),
                              json.dumps(dict(),
                                         ensure_ascii=False),
                              content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + token})
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)

        urlStr = self.urlPrefix + 'engagement/${uuid}/activities/'
        response = self.c.get(urlStr.replace('${uuid}', str(
            self.engagement.uuid)), **{'HTTP_AUTHORIZATION': "token " + token})
        content = json.loads(response.content)
        self.assertEqual(len(content), 2)

        message = DailyScheduledMessage()
        bus_service.send_message(message)
        self.assertTrue(self.is_digested_mock_sent)
        self.assertEqual(self.message, message)
