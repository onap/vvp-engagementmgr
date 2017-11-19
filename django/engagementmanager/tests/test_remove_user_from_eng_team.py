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
from rest_framework.status import HTTP_204_NO_CONTENT
from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class TestEngagementSetStage(TestBaseEntity):

    def childSetup(self):

        self.createVendors([Constants.service_provider_company_name,
                            'Amdocs'])
        self.vendor = Vendor.objects.get(name='Amdocs')
        self.service_provider = Vendor.objects.get(
            name=Constants.service_provider_company_name)
        self.createDefaultRoles()

        # For negative tests
        self.user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'user',
            self.standard_user,
            True)
        self.user2 = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'user2',
            self.standard_user,
            True)
        # Create users with role el (el+peer reviwer)
        self.el_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'el user',
            self.el,
            True)
        self.peer_reviewer = self.creator.createUser(
            self.service_provider,
            self.randomGenerator("main-vendor-email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.el,
            True)
        # Create a user with admin role
        self.admin_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            Constants.service_provider_admin_mail,
            '55501000199',
            'admin user',
            self.admin,
            True)

        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.engagement_team.add(
            self.el_user, self.user, self.user2)
        self.engagement.save()

        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"),
            self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(
            self.randomGenerator("randomString"),
            self.engagement,
            self.deploymentTarget,
            False,
            self.vendor)

        self.data = dict()
        self.user_token = self.loginAndCreateSessionToken(self.user)
        self.user2_token = self.loginAndCreateSessionToken(self.user2)
        self.admin_token = self.loginAndCreateSessionToken(self.admin_user)

    def loggerTestFailedOrSucceded(self, bool_flag):
        if bool_flag:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug(" Test Succeeded")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        else:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug("Test failed")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

    def test_remove_user_from_eng_team_by_admin(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test 2 started: Admin removes user from the eng team!")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.get_engagement_url = self.urlPrefix + \
            "single-engagement/" + str(self.engagement.uuid)
        self.urlStr = self.urlPrefix + "engagements/engagement-team/"
        self.data['eng_uuid'] = str(self.engagement.uuid)
        self.data['user_uuid'] = str(self.user.uuid)

        datajson = json.dumps(self.data, ensure_ascii=False)

        logger.debug(
            "**************************************************")
        logger.debug("----- sending put request with body -----")
        logger.debug(
            "**************************************************")

        response = self.c.put(self.urlStr,
                              datajson,
                              content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token "
                                 + self.admin_token})
        if (response.status_code != HTTP_204_NO_CONTENT):
            print(response.status_code)
        response2 = self.c.get(self.get_engagement_url,
                               {},
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token "
                                  + self.admin_token})

        # Check if the user it still in the engagement team
        received_eng = json.loads(response2.content)
        found = False
        for item in received_eng["engagement"]["engagement_team"]:
            if (self.user.email == item["email"]):
                found = True
                break
        if found:
            self.loggerTestFailedOrSucceded(False)
            self.assert_(False, "user is still in the eng_team")
        else:
            self.loggerTestFailedOrSucceded(True)

    def test_negative_remove_user_from_eng_team_by_another_user(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Test 3 (Negative) started: User2 removes \
            user1 from the eng team!")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.get_engagement_url = self.urlPrefix + \
            "single-engagement/" + str(self.engagement.uuid)
        self.urlStr = self.urlPrefix + "engagements/engagement-team/"
        self.data['eng_uuid'] = str(self.engagement.uuid)
        self.data['user_uuid'] = str(self.user.uuid)

        datajson = json.dumps(self.data, ensure_ascii=False)

        logger.debug(
            "**************************************************")
        logger.debug("----- sending put request with body -----")
        logger.debug(
            "**************************************************")

        response = self.c.put(self.urlStr,
                              datajson,
                              content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token "
                                 + self.user2_token})
        if (response.status_code != HTTP_204_NO_CONTENT):
            print(response.status_code)
        response2 = self.c.get(self.get_engagement_url,
                               {},
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token "
                                  + self.admin_token})

        # Check if the user it still in the engagement team(it is supposed to
        # remain there)
        received_eng = json.loads(response2.content)
        found = False
        for item in received_eng["engagement"]["engagement_team"]:
            if (self.user.email == item["email"]):
                found = True
                break
        if not found:
            self.loggerTestFailedOrSucceded(False)
            self.assert_(False, "user is NOT in the eng_team")
        else:
            self.loggerTestFailedOrSucceded(True)

    def test_negative_remove_el_user_from_eng_team_by_admin(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Test 4 (Negative) started: admin removes \
            el_user from the eng team!")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.get_engagement_url = self.urlPrefix + \
            "single-engagement/" + str(self.engagement.uuid)
        self.urlStr = self.urlPrefix + "engagements/engagement-team/"
        self.data['eng_uuid'] = str(self.engagement.uuid)
        self.data['user_uuid'] = str(self.el_user.uuid)

        datajson = json.dumps(self.data, ensure_ascii=False)

        logger.debug(
            "**************************************************")
        logger.debug("----- sending put request with body -----")
        logger.debug(
            "**************************************************")

        response = self.c.put(self.urlStr,
                              datajson,
                              content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token "
                                 + self.admin_token})
        if (response.status_code != HTTP_204_NO_CONTENT):
            print(response.status_code)
        response2 = self.c.get(self.get_engagement_url,
                               {},
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token "
                                  + self.admin_token})

        # Check if the user it still in the engagement team(it is supposed to
        # remain there)
        received_eng = json.loads(response2.content)
        found = False
        for item in received_eng["engagement"]["engagement_team"]:
            if (self.el_user.email == item["email"]):
                found = True
                break
        if not found:
            self.loggerTestFailedOrSucceded(False)
            self.assert_(False, "el user was NOT found in the eng_team")
        else:
            self.loggerTestFailedOrSucceded(True)
