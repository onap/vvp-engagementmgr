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
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.apps import bus_service
from engagementmanager.bus.messages.activity_event_message import \
    ActivityEventMessage
from engagementmanager.models import Vendor
from engagementmanager.utils.constants import Constants
from engagementmanager.utils.activities_data import \
    UserJoinedEngagementActivityData
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class NotificationsTestCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])

        self.createDefaultRoles()
        # Create a user with role el
        vendor = Vendor.objects.get(
            name=Constants.service_provider_company_name)
        self.peer_reviewer = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'peer-reviewer user',
            self.el,
            True)
        self.el_user = self.creator.createUser(
            vendor,
            self.randomGenerator("main-vendor-email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.el,
            True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.el_user.uuid))
        print('Full Name: ' + self.el_user.full_name)
        print('-----------------------------------------------------')

        # Create a user with role standard_user
        vendor = Vendor.objects.get(name='Other')
        self.user = self.creator.createUser(
            vendor,
            self.randomGenerator("email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.standard_user,
            True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.user.uuid))
        print('Full Name: ' + self.user.full_name)
        print('-----------------------------------------------------')

        # Create an Engagement with team
        self.engagement = self.creator.createEngagement(self.randomGenerator(
            "randomString"), self.randomGenerator("randomString"), None)
        self.engagement.engagement_team.add(self.user, self.el_user)
        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement.uuid))
        print('-----------------------------------------------------')
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_reviewer
        # Create a VF
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"),
            self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(
            self.randomGenerator("randomString"),
            self.engagement,
            self.deploymentTarget,
            False,
            vendor)

        print('-----------------------------------------------------')
        print('Created VF:')
        print('UUID: ' + str(vendor.uuid))
        print('-----------------------------------------------------')

        self.token = self.loginAndCreateSessionToken(self.user)

    def testPullNotifications(self):

        urlStr = self.urlPrefix + 'notifications/'

        logger.debug("Starting pull notification test")
        logger.debug("Creating a random new user")
        vendor = Vendor.objects.get(name='Other')
        randomUser = self.creator.createUser(
            vendor,
            self.randomGenerator("email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.standard_user,
            True)
        self.engagement.engagement_team.add(randomUser)
        self.engagement.save()

        logger.debug(
            "created a new user & added them to the engagement team, \
            going to create the activity and consider it as a notification")
        usersList = []
        usersList.append(randomUser)
        activity_data = UserJoinedEngagementActivityData(
            self.vf, usersList, self.engagement)
        bus_service.send_message(ActivityEventMessage(activity_data))

        response = self.c.get(urlStr + str(randomUser.uuid) +
                              "/0/1", **{'HTTP_AUTHORIZATION':
                                         "token " + self.token})
        content = response.content
        status = response.status_code
        logger.debug("Got response : " + str(status))
        logger.debug("Got response : " + str(content))
        if (status != 200):
            logger.error("Got response : " + str(status) +
                         " , wrong http response returned ")
            self.assertEqual(response.status_code, 200)
        logger.debug("Ended pullNotifications test ")
