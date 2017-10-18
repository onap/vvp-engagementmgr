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
from engagementmanager.bus.messages.activity_event_message import ActivityEventMessage
from engagementmanager.models import Vendor
from engagementmanager.utils.activities_data import UserJoinedEngagementActivityData
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants
from engagementmanager.apps import bus_service
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class ActivityTestCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])

        self.createDefaultRoles()
        # Create a user with role el
        vendor = Vendor.objects.get(name=Constants.service_provider_company_name)
        self.el_user = self.creator.createUser(vendor, self.randomGenerator(
            "main-vendor-email"), self.randomGenerator("randomNumber"), self.randomGenerator("randomString"), self.el, True)
        vendor = Vendor.objects.get(name='Other')
        self.user = self.creator.createUser(vendor, self.randomGenerator("email"), self.randomGenerator(
            "randomNumber"), self.randomGenerator("randomString"), self.standard_user, True)
        self.pruser = self.creator.createUser(vendor, self.randomGenerator("email"), self.randomGenerator(
            "randomNumber"), self.randomGenerator("randomString"), self.standard_user, True)

        # Create an Engagement with team
        self.engagement = self.creator.createEngagement(self.randomGenerator(
            "randomString"), self.randomGenerator("randomString"), None)
        self.engagement.engagement_team.add(self.user, self.el_user)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.pruser
        self.engagement.save()

        # Create a VF
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"), self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(self.randomGenerator("randomString"),
                                        self.engagement, self.deploymentTarget, False, vendor)
        self.token = self.loginAndCreateSessionToken(self.user)

    def testCreateActivity(self):
        urlStr = self.urlPrefix + 'engagement/${uuid}/activities/'
        logger.debug("Starting Activity & notification creation test")

        logger.debug("Starting activity test: User joined")
        vendor = Vendor.objects.get(name='Other')
        randomUser = self.creator.createUser(vendor, self.randomGenerator("email"), self.randomGenerator(
            "randomNumber"), self.randomGenerator("randomString"), self.standard_user, True)
        self.engagement.engagement_team.add(randomUser)
        self.engagement.save()

        logger.debug(
            "created a new user & added them to the engagement team, going to create the activity and consider it as a notification")
        usersList = []
        usersList.append(randomUser)
        activity_data = UserJoinedEngagementActivityData(self.vf, usersList, self.engagement)
        bus_service.send_message(ActivityEventMessage(activity_data))
        logger.debug(
            "activity & notification created successfully, please manually verify that an email was sent / MX server tried to send")
        logger.debug("Ended activity test: User joined ")

        logger.debug("Starting pullActivities test")
        response = self.c.get(urlStr.replace('${uuid}', str(self.engagement.uuid)),
                              **{'HTTP_AUTHORIZATION': "token " + self.token})
        content = response.content
        status = response.status_code
        logger.debug("Got response : " + str(status))
        logger.debug("Got content : " + str(content))
        if (status != 200):
            logger.error("Got response : " + str(status) + " , wrong http response returned ")
            self.assertEqual(response.status_code, 200)
        logger.debug("Ended pullActivities test ")

        logger.debug("Starting activity test: delete user")
        logger.debug("Verify that the 'User Joined' activity is deleted from the recent activities")
        response = self.c.get(urlStr.replace('${uuid}', str(self.engagement.uuid)),
                              **{'HTTP_AUTHORIZATION': "token " + self.token})
        content = response.content
        status = response.status_code
        logger.debug("Got response : " + str(status))
        logger.debug("Got content : " + str(content))
        if (status != 200):
            logger.error("Got response : " + str(status) + " , wrong http response returned ")
            self.assertEqual(response.status_code, 200)
        logger.debug("Ended activity test: delete user ")
