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
from uuid import uuid4
from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_200_OK
from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class EngagementStatusTestCase(TestBaseEntity):

    def childSetup(self):  # Variables to use in this class.
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()
        self.admin, self.el, self.standard_user = self.creator.createAndGetDefaultRoles()

        # Create a user with role el
        self.el_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"),
            '55501000199', 'el user', self.el, True)
        self.peer_review_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
        # Create a user with role standard_user
        self.user = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'user', self.standard_user, True)
        self.user_not_team = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'user not team', self.standard_user, True)
        # Create an Engagement with team
        self.engagement = self.creator.createEngagement(uuid4(), 'Validation', None)
        self.engagement.engagement_team.add(self.user, self.el_user)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_review_user
        self.engagement.save()
        self.token = self.loginAndCreateSessionToken(self.user)
        self.ELtoken = self.loginAndCreateSessionToken(self.el_user)
        self.user_not_team_token = self.loginAndCreateSessionToken(self.user_not_team)

        urlStr = self.urlPrefix + 'engagements/${uuid}/status'
        myjson = json.dumps({"description": "blah blah"}, ensure_ascii=False)
        response = self.c.post(urlStr.replace('${uuid}', str(self.engagement.uuid)), myjson,
                               content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        self.created_status = json.loads(response.content)

    def testPutStatus(self):
        urlStr = self.urlPrefix + 'engagements/${uuid}/status'

        self.printTestName("START - testPutStatus")

        logger.debug("action should fail (401), Only Engagement Lead can set Engagement Progress")

        myjson = json.dumps(
            {"eng_status_uuid": self.created_status['uuid'], "description": "blah2 blah2"}, ensure_ascii=False)
        response = self.c.put(urlStr.replace('${uuid}', str(self.engagement.uuid)), myjson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

        myjson = json.dumps(
            {"eng_status_uuid": self.created_status['uuid'], "description": "blah2 blah2"}, ensure_ascii=False)
        response = self.c.put(urlStr.replace('${uuid}', str(self.engagement.uuid)), myjson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.printTestName("END - testPutStatus")

    def testPostStatus(self):
        urlStr = self.urlPrefix + 'engagements/${uuid}/status'

        self.printTestName("START - testPostStatus")

        logger.debug("action should fail (401), Only Engagement Lead can set Engagement Progress")

        myjson = json.dumps({"description": "blah blah"}, ensure_ascii=False)
        response = self.c.post(urlStr.replace('${uuid}', str(self.engagement.uuid)), myjson,
                               content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

        logger.debug("action should fail (400), For fake engagement uuid")
        myjson = json.dumps({"description": "blah blah"}, ensure_ascii=False)
        response = self.c.post(urlStr.replace(
            '${uuid}', str(uuid4())), myjson, content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

        myjson = json.dumps({"description": "blah blah"}, ensure_ascii=False)
        response = self.c.post(urlStr.replace('${uuid}', str(self.engagement.uuid)), myjson,
                               content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.printTestName("END - testPostStatus")

    def testGetStatus(self):
        urlStr = self.urlPrefix + 'engagements/${uuid}/status'

        self.printTestName("START - testGetStatus")

        response = self.c.get(urlStr.replace('${uuid}', str(self.engagement.uuid)),
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        logger.debug("action should fail (401), Only team members can get status")

        response = self.c.get(urlStr.replace('${uuid}', str(
            self.engagement.uuid)), content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.user_not_team_token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

        logger.debug("action should fail (401), Only existing eng_uuid cab ne fetched")
        response = self.c.get(urlStr.replace('${uuid}', str(
            uuid4())), content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

        self.printTestName("END - testGetStatus")
