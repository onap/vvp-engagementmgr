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
from rest_framework.status import HTTP_401_UNAUTHORIZED, \
    HTTP_202_ACCEPTED, HTTP_500_INTERNAL_SERVER_ERROR
from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class EngProgressTestCase(TestBaseEntity):

    def childSetup(self):  # Variables to use in this class.
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()
        self.admin, self.el, self.standard_user = \
            self.creator.createAndGetDefaultRoles()

        # Create a user with role el
        self.el_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'el user',
            self.el,
            True)
        self.peer_reviewer = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
        # Create a user with role standard_user
        self.user = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'user', self.standard_user, True)
        # Create an Engagement with team
        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.engagement_team.add(self.user, self.el_user)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.save()
        self.token = self.loginAndCreateSessionToken(self.user)
        self.ELtoken = self.loginAndCreateSessionToken(self.el_user)

    def testSetProgress(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/progress'

        self.printTestName("START")

        logger.debug(
            "action should fail (401), Only Engagement \
            Lead can set Engagement Progress")
        response = self.c.put(
            urlStr,
            '{ "progress" : 50 }',
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

        response = self.c.put(
            urlStr,
            '{ "progress" : 50 }',
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)

        response = self.c.put(
            urlStr,
            '{ "progress" : 101 }',
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_500_INTERNAL_SERVER_ERROR)

        self.printTestName("END")
